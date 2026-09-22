# WECARE 3.0 — Device Transfer Code (Re-enroll Already-Enrolled Participant)

## Context
Just implemented and verified: `Participant.generate_enrollment_code()` now generates 5-digit numeric codes (with collision retry), used by the existing "Generate enrollment code (no email)" and "Generate code and email participant" admin actions (`backend/participants/admin.py`, `ParticipantAdmin.actions`).

Those existing actions both filter `queryset.filter(is_enrolled=False)` — they intentionally skip already-enrolled participants, since they're designed for first-time signup only.

**Real use case surfaced by stakeholder:** a participant wants to switch devices (e.g., iPhone to iPad for better viewing) without losing their existing account/data. They need a way to get a fresh enrollment code that logs them into their *same* existing participant record on the new device — not create a duplicate account.

## Requirement

### 1. New admin action: "Generate device transfer code"
Add a new `@admin.action` to `ParticipantAdmin` (in `backend/participants/admin.py`), alongside the existing `generate_code_only` and `generate_and_email_code` actions. This new action:
- Works on **any** participant regardless of `is_enrolled` status (no filter — unlike the existing two actions)
- Calls `generate_enrollment_code()` same as the existing actions (reuses the same 5-digit code generation, no changes needed there)
- Shows a similar success message (e.g., "Generated device transfer code(s) for N participant(s).")

Keep the two existing actions (`generate_code_only`, `generate_and_email_code`) completely unchanged — they still correctly gate on `is_enrolled=False` for genuine first-time signups. This is a third, additional action, not a replacement.

### 2. Backend: modify `POST /api/enroll/` to handle re-enrollment
Currently, the `enroll` view (`backend/participants/views.py`) looks up:
```python
participant = Participant.objects.get(enrollment_code=code, is_enrolled=False)
```
This needs to also match participants who are **already enrolled** but have a valid (non-null) `enrollment_code` set — i.e., someone who just got a device transfer code via the new admin action.

**Updated logic should be:**
- Look up `Participant.objects.get(enrollment_code=code)` — WITHOUT the `is_enrolled=False` filter, since we now need to match both first-time enrollees AND already-enrolled participants using a transfer code.
- **If `participant.is_enrolled` is already `True`** (this is a device-transfer case):
  - Do NOT create a new `User` — reuse the existing `participant.user`
  - Do NOT change `enrolled_at` (should stay as the original enrollment date)
  - **Reuse the existing token** rather than deleting/reissuing it — per stakeholder decision, both old and new devices should stay valid simultaneously for now, sharing one token. Look up the existing `Token` for `participant.user` and return that same token value (don't call `Token.objects.get_or_create` in a way that would create a second one — there should only ever be one token per user given DRF's default `Token` model, so simply fetching the existing one and returning it is correct).
  - Clear the `enrollment_code` after use (still single-use, same as before — a used transfer code shouldn't work twice)
  - Return the same response shape as normal enrollment (token, language, participant_id, week_number, group1/2/3, adrd_relationship_group) — so the mobile app doesn't need any changes, it just gets logged into the existing account transparently
- **If `participant.is_enrolled` is `False`** (normal first-time enrollment): keep all existing behavior completely unchanged — create the `User`, set `is_enrolled=True`, set `enrolled_at`, create a new token, etc., exactly as it currently works.

### What NOT to change
- Do not modify `generate_enrollment_code()` itself — already correct from the previous task, 5-digit codes with collision retry.
- Do not modify the two existing admin actions (`generate_code_only`, `generate_and_email_code`) — they keep their `is_enrolled=False` filter, unchanged.
- Do not implement token deletion/reissuing for the old device — per stakeholder decision, both devices stay logged in with the shared token, for now. (Note in a code comment that this could change later if the team decides old-device logout is preferred — but don't build that now.)
- Do not switch away from DRF's default `Token` model to something like django-rest-knox — out of scope for this task.
- Do not change the mobile app (`EnrollmentScreen.js`, `authService.ts`) — this should work transparently through the existing `/api/enroll/` call with no frontend changes needed, since the response shape stays identical.

## Testing expectations
- Test normal first-time enrollment still works exactly as before (unaffected participant, fresh code, `is_enrolled=False` → `True`, new token, new `enrolled_at`).
- Test the new "Generate device transfer code" admin action on an **already-enrolled** participant — confirm it works (unlike the existing two actions, which should still show "0 participant(s)" for an already-enrolled selection).
- Test calling `POST /api/enroll/` with that transfer code — confirm:
  - It succeeds (200, not 404/400)
  - Returns the SAME token the participant already had (fetch their token before and after, compare — should be identical)
  - `enrolled_at` is unchanged from before the transfer
  - `participant.user` is the same `User` object as before (not a new one)
  - The transfer code is cleared after use (single-use, can't be reused a third time)
- Test that a participant with two "sessions" (old device's stored token + newly issued via transfer code — which are the same token value) can both successfully make authenticated API calls (e.g., both can hit `GET /api/profile/` using that same token) — confirming the "both devices stay logged in" behavior works as intended.
- Run `python manage.py check` to confirm no syntax/import errors.
