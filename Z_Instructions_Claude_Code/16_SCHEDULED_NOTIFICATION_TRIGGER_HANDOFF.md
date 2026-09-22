# WECARE 3.0 — Scheduled Notification Trigger Endpoint (for EventBridge)

## Context
Two related but separate automated-sending features exist:

1. **Daily notification** (just built, fully working) — `POST /api/internal/trigger-daily-notification/` in `backend/content/views.py`, secured via `X-Trigger-Secret` header checked against `settings.DAILY_NOTIFICATION_TRIGGER_SECRET`. Meant to be called frequently (e.g., every 15 min) by AWS EventBridge; internally checks "has today's send time passed, and have we not already sent today" before actually sending.

2. **One-time scheduled notifications** (built earlier, admin UI works) — the "Send Notification" admin page (`send_notification_view` in `backend/participants/admin.py`) lets an admin pick "Schedule for later," which calls `schedule_notification`/`schedule_notification_bulk` (`backend/participants/notifications.py`) to create `NotificationLog` rows with `status="pending"` and a future `scheduled_for` datetime. **The actual sending of these currently only happens via a manual management command**, `backend/participants/management/commands/send_scheduled_notifications.py`, which someone has to run by hand (`python manage.py send_scheduled_notifications`). There is currently NO HTTP endpoint for this — unlike the daily notification feature, this one can't be triggered by EventBridge yet, since EventBridge calls HTTP endpoints, not management commands directly.

**This task closes that gap** — add an HTTP endpoint that does the same thing the management command does, so EventBridge can trigger it the same way it'll trigger the daily notification check.

## Requirement

### Add a new endpoint that wraps the existing management command's logic
In `backend/content/views.py` (same file as `trigger_daily_notification_check`, for consistency — or `participants/views.py` if that's a better fit given `send_scheduled_notifications` currently lives in the `participants` app's management commands; use your judgment, but keep it consistent with wherever makes more sense given the existing command's location), add:

```python
@api_view(["POST"])
@permission_classes([AllowAny])
def trigger_scheduled_notifications(request):
    ...
```

**Security — reuse the exact same shared-secret pattern** already established for the daily notification endpoint:
- Check the same `X-Trigger-Secret` header against the same `settings.DAILY_NOTIFICATION_TRIGGER_SECRET` value (reuse the identical secret/env var — no need for a second, separate secret; both are internal cron-style triggers for the same backend, one shared secret is sufficient and simpler to manage in EventBridge config later).
- Return `403 Forbidden` immediately on missing/wrong secret, matching the daily endpoint's exact behavior.

**Logic inside the view:**
Don't duplicate the actual "find due pending notifications and send them" logic by hand in the view — instead, reuse `send_scheduled_notifications.py`'s existing `Command` class logic directly. Look at how that management command is currently structured (it likely has a `handle()` method containing the core logic) and either:
- Call the management command programmatically via Django's `call_command('send_scheduled_notifications')` from within the view (simplest, most reuse, but check whether the command currently prints results via stdout rather than returning a structured value — if so, this approach won't easily let the view return a JSON summary to the caller), OR
- Refactor the command's core logic into a small reusable function (e.g., in `backend/participants/notifications.py`, alongside the other notification functions) that BOTH the existing management command AND this new view call — this is cleaner if the command's logic is easily extractable, and lets both the CLI command (for manual use) and the new HTTP endpoint return/print the same structured summary. Prefer this approach if it's a reasonably small refactor; fall back to `call_command` if extracting cleanly turns out to be messier than expected.

Either way, the endpoint should return a JSON summary of what happened — e.g., `{"status": "ok", "processed": N, "sent": X, "failed": Y, "skipped_no_token": Z}` (matching the general shape/spirit of the daily endpoint's response and the management command's existing summary print statement).

### Wire the URL
Add the new endpoint's URL pattern alongside the daily notification trigger's URL (same `urls.py` file), e.g. `path("internal/trigger-scheduled-notifications/", views.trigger_scheduled_notifications, name="trigger_scheduled_notifications")`.

## What NOT to change
- Do NOT modify the daily notification endpoint (`trigger_daily_notification_check`) — already correct and verified, this task adds a second, separate endpoint alongside it.
- Do NOT modify `schedule_notification`/`schedule_notification_bulk` — those already correctly create pending rows, unrelated to this task.
- Do NOT remove or deprecate the existing management command (`send_scheduled_notifications.py`) — it should keep working for manual/local use exactly as before, whether you refactor its internals into a shared function or leave it calling that shared function itself.
- Do NOT set up any actual AWS EventBridge rule — still out of scope, this is Django-side only, same as the daily notification task.
- Do NOT introduce a second/different secret — reuse `DAILY_NOTIFICATION_TRIGGER_SECRET` for both endpoints, per the note above.

## Testing expectations
- Schedule a notification a few minutes in the future via the existing admin "Send Notification" page (Schedule for later) — confirm it's created as `pending`.
- POST to the new endpoint with the correct secret BEFORE the scheduled time passes — confirm it correctly reports 0 processed (nothing due yet), and does NOT send early.
- Wait for the scheduled time to pass (or set up a test scenario with an already-past `scheduled_for`, similar to how the original scheduling feature was tested) — POST again — confirm it now sends, updates the `NotificationLog` row's status in place (not a duplicate row), and the real device receives the notification.
- POST with a missing/wrong secret — confirm `403 Forbidden`.
- POST when there's nothing due — confirm it cleanly reports 0 processed with no errors (idempotent/safe to call repeatedly, same spirit as the daily endpoint, though this one doesn't need the same "already sent today" tracking since each individual `NotificationLog` row's own status already prevents it from being processed twice).
- Confirm the existing manual management command (`python manage.py send_scheduled_notifications`) still works exactly as before, whether directly or via the shared refactored function.
- Run `python manage.py check`.
