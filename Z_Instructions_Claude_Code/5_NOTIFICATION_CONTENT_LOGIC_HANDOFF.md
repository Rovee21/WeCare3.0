# WECARE 3.0 — Notification Content/Message Logic

## Context
Building on two already-implemented and verified pieces:
- `backend/participants/notifications.py` — `send_push_notification(participant, title, body, data=None)` and `send_push_notification_bulk(participants, title, body, data=None)`. These are pure sending functions, tested via Django shell, not yet wired into any UI or model.
- `NotificationLog` model already exists in `backend/content/models.py`:
```python
class NotificationLog(models.Model):
    TYPE_DAILY = "daily"
    TYPE_UNREAD = "unread_reminder"
    TYPE_VJ = "vj_reminder"
    TYPE_CHOICES = [
        (TYPE_DAILY, "Daily Session"),
        (TYPE_UNREAD, "24hr Unread Reminder"),
        (TYPE_VJ, "Voice Journal Reminder"),
    ]
    participant = models.ForeignKey("participants.Participant", on_delete=models.CASCADE, related_name="notification_logs")
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    push_up = models.CharField(max_length=200, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    opened_at = models.DateTimeField(null=True, blank=True)
```
Note: `push_up` appears to be the message/title field (naming seems to come from an older draft naming convention — check `NotificationLogAdmin` in `backend/content/admin.py` for how it's currently displayed/labeled, to understand existing conventions before changing anything).

This task defines HOW a notification gets composed and connects to actual sending. It's still NOT the admin UI (that's the next task after this) — this task is about the data model / structure that represents "a notification to send," decided as **freeform text** (not predefined templates) per stakeholder decision.

## Requirement

### Decision confirmed: Freeform messaging
Admins will type a custom title + body each time they send a notification — no predefined templates for now. Keep this simple.

### What to build

**1. Reconsider `NotificationLog`'s role**
Currently `NotificationLog` seems designed as a per-send audit record (one row = one notification sent to one participant, with `sent_at` and `opened_at` tracking). Confirm this model is suitable to serve as BOTH:
(a) the record of a notification that was sent (audit trail — already its apparent purpose), and
(b) potentially, the record of a notification that's scheduled to send in the future (needed for the next task, one-time scheduling — but that's the NEXT task, not this one).

For THIS task, focus on (a) only: wiring `send_push_notification` results into `NotificationLog` for immediate/direct sends. Add whatever fields are missing to make this work well — e.g., you may need a `title` field distinct from `push_up`/body if it doesn't already cleanly separate title vs. body (check current field meaning first, don't assume). You may also want a `status` field (e.g., `sent`, `failed`, `skipped_no_token`) since `send_push_notification` returns exactly that kind of result and it'd be a shame to lose it.

**2. Create a helper function that ties sending + logging together**
Something like `backend/participants/notifications.py` (extend the existing file) or wherever fits:
```python
def send_and_log_notification(participant, title, body, notification_type="daily"):
    """
    Sends a push notification via send_push_notification() and creates
    a NotificationLog record reflecting the outcome (success/failure/no_token).
    Returns the NotificationLog instance created.
    """
```
And a bulk equivalent:
```python
def send_and_log_notification_bulk(participants, title, body, notification_type="daily"):
    """
    Sends to multiple participants, creating one NotificationLog row per participant,
    each reflecting that participant's individual send outcome.
    Returns a summary dict (reuse/extend the shape from send_push_notification_bulk)
    plus the list of NotificationLog instances created.
    """
```

**3. Decide on `notification_type` handling for freeform/manual sends**
Since this is freeform (not template-driven), the existing `TYPE_CHOICES` (`daily`, `unread_reminder`, `vj_reminder`) may not have a good fit for "an admin just wrote something ad-hoc." Consider adding a new choice like `TYPE_MANUAL = "manual"` / `("manual", "Manual / Ad-hoc")` to the model's `TYPE_CHOICES`, so freeform admin-composed notifications have an accurate category, distinct from the automated-trigger types that don't exist yet (those come later in the daily-reminder task, item 6 on the roadmap — not this task). If you add this, it requires a migration — that's fine and expected here.

## What NOT to build yet
- Do NOT build the Django Admin UI for composing/sending notifications yet — that's the next task after this one.
- Do NOT build scheduling (future `sent_at`) — this task is only about immediate/direct sends being properly logged. Scheduling is a separate later task.
- Do NOT build the automatic daily reminder trigger logic — that's the final task on the roadmap, deliberately last.
- Do NOT change `send_push_notification` or `send_push_notification_bulk` themselves (from the previous task) — wrap/call them, don't modify their internals, unless a genuine bug is found (unlikely, they were tested and verified already).

## Testing expectations
- Call `send_and_log_notification` directly via Django shell against a real participant with a valid token — confirm the notification arrives on the physical device AND a `NotificationLog` row is created with the correct participant, title/body, type, and a status reflecting success.
- Call it against a participant with no token — confirm no crash, and confirm a `NotificationLog` row is still created reflecting the `no_token` outcome (don't silently lose the fact that a send was attempted — audit trail matters for a research study).
- Call `send_and_log_notification_bulk` against a mix of participants — confirm one `NotificationLog` row per participant, each with accurate individual status, and confirm the physical device(s) with valid tokens actually receive the notification.
- Run `python manage.py check` and confirm any new migration applies cleanly.
- Check `backend/content/admin.py`'s existing `NotificationLogAdmin` still displays sensibly with any new/changed fields (don't need to redesign it, just confirm it doesn't break/look broken).
