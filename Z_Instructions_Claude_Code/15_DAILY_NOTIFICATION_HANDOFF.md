# WECARE 3.0 — Admin-Configurable Daily Notification (Django Side)

## Context
Push notification infrastructure is fully built and verified from earlier tasks:
- `backend/participants/notifications.py`: `send_push_notification`, `send_push_notification_bulk`, `send_and_log_notification`, `send_and_log_notification_bulk`, `schedule_notification`, `schedule_notification_bulk`.
- `NotificationLog` model (`backend/content/models.py`) with `status` (`pending`/`sent`/`failed`/`skipped_no_token`), `scheduled_for`, `actually_sent_at`, `title`, `push_up` (body), `notification_type` (includes `TYPE_MANUAL`).
- Full admin UI for composing/sending one-off notifications (single participant / cohort / everyone / selected participants, send-now or schedule-later) — `send_notification_view` in `backend/participants/admin.py`.
- Cohort-based content scheduling (`Participant.is_waitlisted()`, `program_start_date()`, `automatic_gated_week()`) — content unlocks at midnight local time based on the cohort's start date, fully independent of any notification. Confirmed design decision: this daily notification task does NOT change when content unlocks — it's purely a reminder layered on top.

This task builds the **automated daily reminder** — an admin sets one time-of-day (e.g., 7:00 PM), and every day at that time, all enrolled, non-waitlisted participants automatically receive a (admin-customizable) notification. This is the "8am daily scheduling" item from the original roadmap, refined per stakeholder discussion into an admin-configurable time rather than a hardcoded 8am.

**Important operational note:** the developer testing this does NOT have deploy access to the live AWS-hosted admin (`https://admin.wecare-admin.me/admin/`) — all testing must happen against the local Docker setup (`docker-compose up` in `backend/`). The actual AWS EventBridge wiring (a separate, later step) will be handled once this Django-side implementation is complete and verified locally.

## Requirement

### 1. Add a settings model for the daily notification config
Add a new small model to `backend/content/models.py` (or `participants/models.py` — pick whichever fits your judgment of the codebase's existing organization; `content` seems more fitting since `NotificationLog` already lives there), e.g.:

```python
class DailyNotificationSettings(models.Model):
    send_time = models.TimeField(default="19:00", help_text="Time of day (in the server's local timezone) the daily reminder is sent to all enrolled, non-waitlisted participants.")
    title = models.CharField(max_length=200, default="Your session is ready!", help_text="Notification title. Customizable by admin.")
    body = models.CharField(max_length=200, default="Come check out today's session in the WeCare app.", help_text="Notification body text. Customizable by admin.")
    is_enabled = models.BooleanField(default=True, help_text="If unchecked, no daily notifications will be sent, regardless of time.")
    last_sent_date = models.DateField(null=True, blank=True, help_text="The date the daily batch was last sent — used internally to prevent sending twice in the same day.")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Daily notification — {self.send_time} ({'enabled' if self.is_enabled else 'disabled'})"
```

**This should be a singleton-style model** — there's only ever one row (one global daily-notification config, not per-cohort or per-participant). Enforce this simply: in the admin (see below), only allow editing the existing row, don't let admins create multiple rows — either via `has_add_permission` returning `False` once a row exists, or by just seeding one row via a data migration / `get_or_create` pattern wherever it's read. Use your judgment on the cleanest way to enforce "only one row ever," but don't over-engineer it.

Requires a migration. Also consider a data migration (or `get_or_create` in the admin/view logic) to ensure exactly one row exists by default, so the feature works out of the box without requiring a manual first-time setup step.

### 2. Register in Django Admin, under Content
Add a simple `DailyNotificationSettingsAdmin` in `backend/content/admin.py` (or wherever `NotificationLogAdmin` etc. live), with an editable form for `send_time`, `title`, `body`, `is_enabled`. Per stakeholder request, this should be reachable as its own clear item in the admin, positioned/labeled so it reads naturally as being "under Content" on the admin home page (Django's default admin index already groups models by app — since this lives in the `content` app, it'll naturally appear grouped there, which satisfies "under Content on the home dashboard").

### 3. Add the trigger endpoint
Add a new view, e.g. `backend/content/views.py` (or `participants/views.py` if more consistent with where other internal/cron-style endpoints might live — check for precedent, otherwise your call), something like:

```python
@api_view(["POST"])
@permission_classes([AllowAny])  # secured via shared-secret header instead, see below
def trigger_daily_notification_check(request):
    ...
```

**Security — shared secret header, not open access:**
This endpoint will eventually be called by AWS EventBridge, an automated system, not a logged-in user — so standard token auth doesn't apply. Protect it with a shared secret instead:
- Read an expected secret from a new environment variable, e.g. `DAILY_NOTIFICATION_TRIGGER_SECRET` (add to `backend/wecare/settings/base.py` reading via `env(...)`, similar to how other secrets like `SECRET_KEY` are read).
- The view should check for a header (e.g., `X-Trigger-Secret`) matching that value; if missing or wrong, return `403 Forbidden` immediately without doing anything else.
- For LOCAL testing (since there's no real EventBridge yet), the developer will just call this endpoint manually with `requests`/curl including the correct header — make sure the local `.env`/`docker-compose.yml` has a placeholder value for this new env var so local testing works (reuse the existing pattern where `docker-compose.yml` provides local dev defaults via `${VAR:-default}` syntax, established in an earlier deployment-fix task).

**Logic inside the view, once authenticated:**
1. Fetch the singleton `DailyNotificationSettings` row. If `is_enabled` is `False`, return early (e.g., `{"status": "disabled"}`, 200 OK — not an error, just a no-op).
2. Get the current local time and date (use Django's timezone-aware `now()`, respecting whatever `TIME_ZONE` is configured in settings — check current setting, don't assume UTC vs a specific US timezone without confirming).
3. **Idempotency check:** if `last_sent_date == today`, return early (already sent today, e.g., `{"status": "already_sent_today"}`) — this is what prevents duplicate sends if EventBridge checks in multiple times before/after the target time.
4. **Time check:** if the current time has NOT yet reached `send_time` today, return early (e.g., `{"status": "not_yet_time"}`) — no-op, waiting for a later check-in to actually trigger the send.
5. **If enabled, not yet sent today, and current time >= send_time:** fetch all participants who are enrolled (`is_enrolled=True`) AND not waitlisted (`not participant.is_waitlisted()`) — iterate/filter efficiently, avoid N+1 queries if reasonably easy (checking `is_waitlisted()` per-participant may require per-participant queries given how that method is implemented from the earlier cohort task — check its current implementation and optimize if straightforward, but don't block this task on a deep performance rewrite if it's not trivial; correctness first).
6. Send the configured `title`/`body` to all of them via the existing `send_and_log_notification_bulk` function (reuse it — don't duplicate sending logic), using `notification_type=NotificationLog.TYPE_DAILY` (already exists as a choice on the model, currently unused — this is exactly the case it was designed for).
7. Update `last_sent_date = today` on the settings row and save, so step 3 correctly blocks further sends today.
8. Return a summary response (e.g., `{"status": "sent", "sent": N, "skipped_no_token": M, "failed": K}`).

### 4. Wire the URL
Add the new endpoint's URL pattern to whichever `urls.py` is appropriate (likely `backend/content/urls.py` or `backend/participants/urls.py`, matching wherever the view itself was placed) — something like `path("internal/trigger-daily-notification/", views.trigger_daily_notification_check, name="trigger_daily_notification")`.

## What NOT to build in this task
- Do NOT set up the actual AWS EventBridge rule — that's a separate, later infrastructure step, out of scope here. This task only builds the Django-side endpoint that EventBridge will eventually call.
- Do NOT change anything about how content unlocking works (`is_waitlisted`, `automatic_gated_week`, midnight-based day gating) — confirmed unchanged, this notification is purely an additive reminder layer.
- Do NOT build any per-participant customization of the daily message (e.g., referencing their specific unlocked session by name) — per stakeholder decision, keep it a single admin-configurable message sent identically to everyone eligible, for now.
- Do NOT build a UI for viewing daily-notification send history beyond what already exists — the `NotificationLog` rows created by this feature (with `notification_type=TYPE_DAILY`) will already show up in the existing `NotificationLogAdmin` list view, no new reporting UI needed.

## Testing expectations
- Manually POST to the new endpoint locally with the correct secret header — with `send_time` set to a time already in the past today, `is_enabled=True`, `last_sent_date` not today — confirm it actually sends to all enrolled/non-waitlisted participants (check real device delivery if a valid push token is available, same as previous notification testing) and creates `NotificationLog` rows with `notification_type=daily`.
- Immediately POST again — confirm it now returns "already_sent_today" and does NOT send a second batch (idempotency works).
- Set `send_time` to a time in the FUTURE (later today) — reset `last_sent_date` to null or yesterday — POST again — confirm it returns "not_yet_time" and does not send.
- Set `is_enabled=False` — confirm POSTing returns "disabled" and never sends regardless of time/date.
- POST without the correct secret header (missing or wrong value) — confirm `403 Forbidden`, no notification sent, no `NotificationLog` created.
- Confirm a waitlisted participant (from the earlier cohort/waitlist feature) is correctly excluded from the daily batch, while a normal enrolled participant is correctly included.
- Run `python manage.py check` and confirm the migration applies cleanly.
