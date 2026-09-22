# WECARE 3.0 — Backend Push Notification Sending Function

## Context
Push notification infrastructure is already partially working and manually verified:
- `Participant.push_token` field exists (CharField, stores Expo push token like `ExponentPushToken[...]`)
- Mobile app registers for push notifications and sends the token to `POST /api/device/register/` (backend/participants/views.py `register_device` view), which saves it to `participant.push_token`
- Firebase project (`wecare3-notifications`) is set up with FCM V1 credentials configured in EAS
- Manual testing via Django shell confirmed that POSTing to `https://exp.host/--/api/v2/push/send` with `{"to": token, "title": ..., "body": ..., "sound": "default"}` successfully delivers a real notification to a physical device
- `requests` library is now in `backend/requirements.txt` (already added, don't touch)

This task is to turn that manually-tested shell snippet into a proper, reusable, reasonably robust backend function that other features (admin-triggered sends, scheduled sends, etc.) can call.

## Requirement

Create a function, suggested location `backend/participants/notifications.py` (new file) or as a method/utility wherever fits the existing code organization best — your call, but keep it importable and reusable from other apps (e.g., `content` app might eventually want to trigger notifications too).

### Function signature (adjust as you see fit, but conceptually):
```python
def send_push_notification(participant, title, body, data=None):
    """
    Sends a push notification to a single participant via Expo's push API.
    Returns a result dict indicating success/failure, and does NOT raise
    on delivery failure (network errors should be caught and reported,
    not crash the caller) — but should raise/log clearly if the participant
    has no push_token at all (can't send, nothing to send to).
    """
```

### Requirements for the function:
1. **Handle missing token gracefully** — if `participant.push_token` is empty/None, don't attempt the API call; return a clear failure result (e.g., `{"success": False, "reason": "no_token"}`) rather than crashing or silently doing nothing.
2. **Call Expo's push API** (`https://exp.host/--/api/v2/push/send`) with the token, title, body, and `sound: "default"`. Support an optional `data` dict parameter for any extra payload (not required to use it anywhere yet, just support passing it through).
3. **Handle the two-stage nature of Expo's API correctly** — the initial POST returns a "ticket" (just means Expo *accepted* the request), not a delivery confirmation. As discovered during manual testing, actual delivery success/failure requires a follow-up call to `https://exp.host/--/api/v2/push/getReceipts` with the ticket ID, which can reveal errors like `DeviceNotRegistered` even when the initial send returned "ok". Decide a reasonable approach: either (a) always do the receipt check inline (adds latency, ~2-3 second wait needed per earlier testing), or (b) just send and return the ticket info, leaving receipt-checking as a separate concern/function for now since real scheduled sending will likely batch many notifications and checking receipts synchronously for each isn't scalable. Prefer (b) — return the ticket ID and initial status only, and note in a comment that receipt-checking could be added later as a separate periodic task if delivery-failure tracking becomes important. Don't over-build this.
4. **Handle HTTP/network failures** (timeouts, connection errors, non-200 responses from Expo) — catch exceptions, return a clear failure result rather than an unhandled exception bubbling up.
5. **Log meaningfully** — use Django's logging (or simple print statements consistent with how the rest of the codebase handles logging, check existing patterns) so failures are visible in `docker-compose logs web` without needing to dig through exception tracebacks.

### Also add a bulk-send helper
Since notifications will eventually be sent to whole cohorts (not just one participant at a time), add a second function:
```python
def send_push_notification_bulk(participants, title, body, data=None):
    """
    Sends the same notification to multiple participants.
    Skips participants with no push_token (don't fail the whole batch for one missing token).
    Returns a summary: e.g. {"sent": 12, "skipped_no_token": 3, "failed": 1}
    """
```
This can just loop and call `send_push_notification` per participant for now — no need for batched API calls to Expo (Expo does support batching multiple recipients in one request, but keep this simple for now; note in a comment that batching could be a future optimization if send volume grows).

## What NOT to build yet
- Do NOT build the admin UI for composing/sending notifications yet — that's a separate, later task.
- Do NOT build any scheduling/cron/Celery mechanism yet — that's also separate, later.
- Do NOT wire this into any views or admin actions yet — this task is ONLY the reusable sending function(s) themselves, tested directly (e.g. via Django shell or a simple management command for manual testing), not yet connected to any UI trigger.

## Testing expectations
- Test the function directly via Django shell against a real participant with a valid, currently-working push token (there should be one from recent manual testing — check `Participant.objects.filter(push_token__isnull=False)`) and confirm a real notification arrives on the physical device, same as the manual testing already done, but now going through the new function instead of raw inline code.
- Test the missing-token case: call it with a participant who has no `push_token`, confirm it returns the expected failure result without raising an exception.
- Test the bulk function with a mix of participants (some with tokens, some without) and confirm the summary counts are accurate.
- Run `python manage.py check` to confirm no syntax/import errors.
