# WECARE 3.0 — One-Time Notification Scheduling

## Context
Building on three already-implemented and verified pieces:
- `backend/participants/notifications.py`:
  - `send_push_notification(participant, title, body, data=None)` / `send_push_notification_bulk(...)` — raw sending, tested.
  - `send_and_log_notification(participant, title, body, notification_type=None)` / `send_and_log_notification_bulk(...)` — sends AND creates a `NotificationLog` row per participant reflecting outcome. Tested and verified, including via the admin list view at `/admin/content/notificationlog/`.
- `NotificationLog` model (`backend/content/models.py`) now has: `participant`, `notification_type` (includes `TYPE_MANUAL = "manual"`), `title`, `push_up` (body text — kept as original field name), `status` (`sent`/`failed`/`skipped_no_token`), `sent_at` (auto_now_add), `opened_at`.

This task adds the ability to schedule a notification for a future send time rather than sending immediately — WITHOUT building any real background task infrastructure yet (no Celery, no cron). Just the data model support + a management command that processes due notifications when run. Automation (making that command run periodically without manual intervention) is explicitly a LATER task — not this one.

## Requirement

### 1. Add scheduling fields to `NotificationLog`
- `scheduled_for` — nullable `DateTimeField`. `None`/null means "send immediately" (existing behavior, unchanged). A future datetime means "don't send yet, wait until this time."
- Add a new status value to the existing `status` field's choices: `"pending"` (in addition to existing `sent`/`failed`/`skipped_no_token`). A notification with `scheduled_for` in the future should be created with `status = "pending"` and NOT actually sent at creation time.
- Consider whether `sent_at` (currently `auto_now_add=True`, meaning it's always set to creation time) is now misleading for scheduled notifications — it would represent "when the row was created" not "when it was actually sent." Decide whether to keep `sent_at` as creation timestamp and add a separate `actually_sent_at` field (nullable, set when the send actually happens), or handle it another way — your call, but make sure the audit trail remains meaningful and unambiguous. This will need a migration either way.

### 2. New function: create a scheduled (not-yet-sent) notification
In `backend/participants/notifications.py`, add something like:
```python
def schedule_notification(participant, title, body, scheduled_for, notification_type=None):
    """
    Creates a NotificationLog row with status='pending' and the given
    scheduled_for datetime, WITHOUT sending anything yet.
    Returns the created NotificationLog instance.
    """
```
And a bulk equivalent:
```python
def schedule_notification_bulk(participants, title, body, scheduled_for, notification_type=None):
    """
    Creates one pending NotificationLog row per participant for the same
    scheduled_for time. Does NOT send anything yet.
    Returns a list of created NotificationLog instances (or a summary dict, your call).
    """
```
If `scheduled_for` is in the past or None when these are called, decide sensible behavior — reasonable options: treat it as "send now" by delegating to the existing `send_and_log_notification`, or raise a clear error requiring the caller to use the immediate-send functions for that case. Pick whichever seems cleaner and document your choice in a docstring/comment.

### 3. Management command to process due notifications
Add `backend/participants/management/commands/send_scheduled_notifications.py` (check if `backend/participants/management/commands/` directory already exists — likely does, given `reset_participant` command exists there already; follow that file's conventions/style).

The command should:
- Query all `NotificationLog` rows where `status = "pending"` and `scheduled_for <= timezone.now()`.
- For each, actually send it via the existing `send_push_notification` logic (reuse it — don't duplicate the Expo API call code), then update that SAME row's status to `sent`/`failed`/`skipped_no_token` based on outcome (don't create a duplicate log row — update the existing pending one in place, since it already represents this notification).
- Print/log a summary when done (e.g., "Processed 5 due notifications: 4 sent, 1 skipped_no_token").
- Should be safe to run repeatedly / do nothing if there's nothing due (idempotent — running it when nothing is due should just report 0 processed, not error).

## What NOT to build yet
- Do NOT set up Celery, cron, AWS EventBridge, or any mechanism to make `send_scheduled_notifications` run automatically/periodically. For now, it is triggered manually — the person testing will run `docker-compose exec web python manage.py send_scheduled_notifications` by hand. Automating this is a deliberately separate, later task.
- Do NOT build the admin UI for composing/scheduling notifications yet — that's the next task after this one.
- Do NOT build the automatic daily-reminder trigger logic (the `TYPE_DAILY`/`TYPE_UNREAD`/`TYPE_VJ` automated triggers) — unrelated to this task, and also later.

## Testing expectations
- Call `schedule_notification` with a `scheduled_for` a few minutes in the future, for a participant with a valid token. Confirm a `NotificationLog` row is created with `status="pending"` and NO notification is sent yet (check your phone — nothing should arrive immediately).
- Run `send_scheduled_notifications` immediately after — confirm it does NOT send yet, since the scheduled time hasn't passed (0 processed).
- Wait until the scheduled time has passed (or, more practically for testing, schedule it for a time already in the past on creation via a script, or wait the few real minutes), then run `send_scheduled_notifications` again — confirm it NOW sends the notification, the phone receives it, and the same `NotificationLog` row updates in place (not a new row) to `status="sent"`.
- Test the "nothing due" case — run the command when no pending notifications exist, confirm it exits cleanly with a "0 processed" style message, no errors.
- Test `schedule_notification_bulk` similarly with a mix of participants (some with/without tokens) and confirm correct per-participant outcomes after the command runs.
- Run `python manage.py check` and confirm any new migration applies cleanly.
