# WECARE 3.0 — Fix current_week_number to Use Cohort Start Date (Follow-up)

## Context
Just implemented: `CohortStartDate` model, `Participant.is_waitlisted()`, `program_start_date()`, and the actual content-gating logic (`automatic_gated_week()`, `unlocked_day_number()`) — all correctly anchored to the cohort's `program_start_date` instead of `enrolled_at`. This part is done and verified.

**One thing was left inconsistent:** `Participant.current_week_number` (the property used in the admin participant list display, and in `/api/enroll/`'s response) still calculates based on `enrolled_at`, not the cohort's `program_start_date`. This is now misleading — it can show a participant on "Week 2" in the admin list even though they're actually waitlisted or on Week 1 per the real content-gating logic, because it's using the wrong anchor date.

Stakeholder wants this simple and low-risk: `current_week_number` should just reflect the SAME anchor date as the real gating logic (`program_start_date`), not introduce any new complexity.

## Requirement

Update `Participant.current_week_number` (the existing property) so it's driven by the cohort's `program_start_date`, not `enrolled_at` — matching the same anchor already used by `automatic_gated_week()`.

**Simple, low-risk approach:**
- If the participant `is_waitlisted()` (no `CohortStartDate` row for their cohort yet, or its date is in the future): `current_week_number` should return something clearly indicating "not started" — `0` is a reasonable choice (simple, sortable, obviously distinct from real week numbers 1-7). Use whatever the stakeholder's "minus one or 0 or whatever, doesn't matter" comment suggests is fine — pick ONE of these (0 is probably clearest for admin list sorting/filtering) and use it consistently. Don't overthink this — 0 is fine.
- If NOT waitlisted (cohort has started): return the same value `automatic_gated_week()` already correctly calculates (or call it directly / reuse its logic — don't duplicate the calendar math, just have `current_week_number` delegate to the existing correctly-anchored calculation).

**Keep this minimal:** this should be a small, contained change to the `current_week_number` property only. Do NOT touch `enrolled_at` itself (still just a signup timestamp, unrelated), do NOT touch the actual gating logic in `automatic_gated_week()`/`unlocked_day_number()` (already correct from the previous task), and do NOT add any new fields or models.

## Where this is used — confirm these stay correct
- Admin participant list (`list_display` in `ParticipantAdmin`) — shows `current_week_number` (or similar) as a column; should now correctly show `0` for waitlisted participants and the real cohort-anchored week for active ones.
- `/api/enroll/`'s response (`participants/views.py`'s `enroll` view) — includes `week_number: participant.current_week_number` in its JSON response; should automatically pick up the fix once the property itself is corrected, no separate change needed there.
- Any other place `current_week_number` is referenced (grep for it to be sure) — should all automatically get the corrected value once the property itself is fixed, since it's a single shared property.

## Testing expectations
- A waitlisted participant (future or missing `program_start_date` for their cohort) → `current_week_number` returns `0`.
- A participant whose cohort started in the past → `current_week_number` returns the correct week number (matching what `automatic_gated_week()` calculates, and matching what the participant actually sees in the app).
- Two participants in the same cohort with different `enrolled_at` values, cohort already started → both show the SAME `current_week_number` (proving `enrolled_at` no longer affects this at all, consistent with everything else in the previous task).
- Confirm the admin participant list displays this correctly.
- Confirm `/api/enroll/`'s response returns the corrected `week_number` value.
- Run `python manage.py check`.
