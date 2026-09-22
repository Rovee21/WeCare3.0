# WECARE 3.0 — 5-Digit Participant Codes

## Context
`Participant` model (`backend/participants/models.py`) currently has `generate_enrollment_code()`:
```python
def generate_enrollment_code(self):
    code = secrets.token_urlsafe(6).upper()[:8]
    self.enrollment_code = code
    self.save(update_fields=["enrollment_code"])
    return code
```
This generates an 8-character alphanumeric code (e.g. `1SDT4ZS0`). Stakeholder wants this changed to a simple 5-digit numeric code instead (e.g. `48213`), easier for participants to type on a phone.

## Requirement
Change `generate_enrollment_code()` to generate a 5-digit numeric code (digits 0-9 only, always exactly 5 characters, so codes like `04821` are valid — pad with leading zeros if needed rather than generating a 4-digit number).

**Uniqueness:** Since `enrollment_code` has `unique=True` on the model already, handle the (rare but possible) case of a collision — retry generation if the code already exists in the database, rather than letting the `save()` call raise an IntegrityError.

**Field length:** Check the current `enrollment_code` field definition (`max_length=50` currently, per earlier model review) — no change needed there since 5 digits comfortably fits, but confirm this explicitly rather than assuming.

## What NOT to change
- Don't change anything about the CSV import flow's use of `generate_enrollment_code()` — it already calls this method and should automatically get 5-digit codes with no other changes needed there.
- Don't change the enrollment view/logic itself (`participants/views.py` `enroll` function) — it already does a case-insensitive `.strip().upper()` lookup; confirm 5-digit numeric codes still work fine with that (they will, digits don't have a case, but verify no other assumption breaks).
- Don't touch anything unrelated to code generation.

## Testing expectations
- Generate a code for a test participant via Django shell or admin action, confirm it's exactly 5 digits, numeric only.
- Test enrollment with the new code format end-to-end (via the existing `POST /api/enroll/` flow or the app) to confirm it still works.
- Confirm the admin's "Generate enrollment code" action still displays/emails the new format correctly.
