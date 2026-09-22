# WECARE 3.0 — Admin "Reset / Allow Resend Today" Control for Daily Notification

## Context
`DailyNotificationSettings` (singleton model, `backend/content/models.py`) has `last_sent_date`, currently shown as a **read-only** field in `DailyNotificationSettingsAdmin` (`backend/content/admin.py`) — it's set automatically by `trigger_daily_notification_check` (`backend/content/views.py`) whenever a daily batch actually sends, and is what prevents a second automatic send on the same calendar day (idempotency).

**Real operational need surfaced during live testing tonight:** an admin needs the ability to manually clear/reset `last_sent_date` on demand — either to re-test the automated pipeline same-day, or, in a real production scenario, to deliberately allow a second genuine daily reminder to go out the same day if the team decides that's needed (e.g., forgot to change the message earlier and wants to resend the corrected version). Currently there is NO way to do this without direct database access, which is a real gap — not something requiring RDS/database console access every time.

## Requirement

### Add an admin action to reset `last_sent_date`
In `backend/content/admin.py`'s `DailyNotificationSettingsAdmin`, add an `@admin.action` that clears `last_sent_date` (sets it to `None`) on the singleton row. Since this settings admin was built to auto-redirect the changelist straight into the single row's edit form (no visible list/checkbox UI, per the singleton-enforcement pattern from the original task), a standard Django admin `action` (which normally requires selecting rows via checkboxes on a list page) won't have an obvious way to be triggered through the normal UI flow.

**Simplest approach given the existing singleton UI pattern:** add a custom button directly on the change form itself, similar in spirit to how `send_notification_view`/`csv_import_view` added custom buttons elsewhere in this admin — but simpler here, since it can likely be done with Django's built-in `save_on_top`/custom `change_form_template` override, OR (probably simpler) by adding a small custom view + URL (same `get_urls()` pattern already used elsewhere in `ParticipantAdmin`, just apply the same pattern here on `DailyNotificationSettingsAdmin`) that does the reset and redirects back to the change form with a success message.

**Concretely:**
1. Add a `get_urls()` override on `DailyNotificationSettingsAdmin` adding a route like `<int:object_id>/reset-last-sent/`.
2. That view: fetch the `DailyNotificationSettings` row by `object_id`, set `last_sent_date = None`, save, show a success message via `self.message_user(...)` (e.g., "Reset — the daily notification can now send again today."), redirect back to the change form.
3. On the change form template (custom `change_form.html` override for this specific admin, following the same override pattern used for `ParticipantAdmin`'s `change_form.html` earlier in the project — check that existing file for the exact `{% block object-tools-items %}` pattern to copy), add a clearly-labeled button, e.g. **"⟳ Allow Resend Today"**, linking to that new URL.

**Make the button's intent unambiguous** — since this has real consequences (could trigger a real notification to real participants moments later, once EventBridge's next check-in happens), the button label and/or a short confirmation message should make clear what it does: it does NOT send anything itself, it just clears the "already sent today" flag so the NEXT scheduled EventBridge check-in (or a manual trigger) will be allowed to send again today.

### Do not weaken the underlying safety logic
Do NOT remove or loosen the `last_sent_date` idempotency check itself in `trigger_daily_notification_check` — that protection stays exactly as is (still checks `last_sent_date == today` and blocks if so). This task only adds an explicit, deliberate ADMIN ACTION to clear that flag when genuinely wanted — the automatic system still defaults to "once per day" unless an admin explicitly intervenes. This preserves safety against accidental EventBridge misfires while giving admins real control when they want it.

## What NOT to change
- Do NOT change `trigger_daily_notification_check`'s core logic (disabled check, time check, idempotency check, sending logic) — untouched, still correct.
- Do NOT add any new model fields — `last_sent_date` already exists, this task just adds an admin-triggered way to clear it.
- Do NOT change how `send_time`, `title`, `body`, `is_enabled` are edited — those stay as normal editable form fields, unchanged.
- Do NOT build a general "send history" or "resend log" feature — out of scope, existing `NotificationLogAdmin` already shows sent notifications.

## Testing expectations
- On the `DailyNotificationSettings` change form in Django Admin, confirm the new "Allow Resend Today" button is visible and clearly labeled.
- Click it with `last_sent_date` currently set to today — confirm it clears to `None`, shows a success message, and the change form reflects the cleared value.
- Immediately after, manually POST to `trigger_daily_notification_check` (or wait for the next EventBridge check-in) — confirm it now correctly sends again (assuming `send_time` has already passed and `is_enabled` is true), rather than returning `already_sent_today`.
- Confirm clicking the button when `last_sent_date` is already `None` doesn't error (idempotent button — clicking it when there's nothing to reset should just be a harmless no-op, still showing a success/confirmation message).
- Run `python manage.py check`.
