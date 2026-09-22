# WECARE 3.0 — Cohort-Based Program Start Date + Waitlist

## Context
`Participant` model (`backend/participants/models.py`) has:
- `enrolled_at` — set the moment a participant enters their code (currently drives ALL content-scheduling logic: `automatic_gated_week()`, `unlocked_day_number()`, `effective_current_week()` in the same file, which calculate week/day unlocking based on days elapsed since `enrolled_at`).
- `cohort` — a `PositiveSmallIntegerField` added in a recent task, representing recruitment wave/area, independent of `group1/group2/group3`.

**Problem:** participants recruited over several weeks (e.g., signed up Aug 10 vs Aug 28) currently each start their individual 7-week content clock immediately on their own signup date — meaning people in the same study cohort end up on different weeks of content at the same calendar time. Stakeholder wants everyone in the same cohort to start their content schedule on the SAME date, regardless of when they individually signed up, with a "waitlist" experience for anyone who's enrolled but whose cohort's start date hasn't arrived yet.

## Requirement

### 1. Add a per-cohort start date, set by admin
This needs a new small model (not a field on `Participant`, since it's a property of the COHORT as a whole, not each individual participant) — something like:

```python
class CohortStartDate(models.Model):
    cohort = models.PositiveSmallIntegerField(unique=True, help_text="Matches Participant.cohort")
    program_start_date = models.DateField(help_text="The date this cohort's Week 1 Day 1 content unlocks for everyone in it, regardless of individual signup date.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cohort {self.cohort} — starts {self.program_start_date}"
```
Put this in `backend/participants/models.py` alongside `Participant`. Requires a migration.

Register it in Django Admin (`backend/participants/admin.py`) as its own simple `ModelAdmin` — a small, standalone list where an admin can see/add/edit `(cohort number, start date)` pairs. Keep it simple: `list_display = ["cohort", "program_start_date", "updated_at"]`, no need for anything fancier (no inlines, no custom views) unless it's trivial to add.

### 2. Keep `enrolled_at` meaning "when they signed up" — unchanged
Do NOT repurpose `enrolled_at`. It continues to be set exactly as now, the moment someone enters their enrollment code — this represents actual signup time, for audit/record purposes. No change to the `enroll` view's handling of it.

### 3. Content-scheduling logic should use the COHORT's start date, not `enrolled_at`
This is the core change. `Participant.automatic_gated_week()` and `Participant.unlocked_day_number()` currently calculate elapsed time using `self.enrolled_at`. Change them to instead use the participant's cohort's `program_start_date` (looked up via the new `CohortStartDate` model) as the anchor point for "day 0" of the content schedule.

**Handle the "not yet started" case (waitlist):**
- If today's date is BEFORE the cohort's `program_start_date` (or if no `CohortStartDate` row exists yet for this participant's cohort at all): the participant should be considered "waitlisted" — not yet able to see ANY content, even Week 1 Day 1.
- Add a new method to `Participant`, e.g. `is_waitlisted()`, returning `True` if the cohort's start date is in the future or unset, `False` otherwise (i.e., `program_start_date <= today`).
- Once the cohort's start date arrives (today >= `program_start_date`), compute days-elapsed as `(today - program_start_date).days` instead of `(today - enrolled_at).days`, and feed that into the existing day/week unlocking math exactly as before — the actual unlocking LOGIC (calendar-day gating, 7-day week gate, sequential-read requirement, session overrides) stays completely unchanged, just the anchor date changes from individual signup time to shared cohort start time.

### 4. Backend: reflect waitlist status in relevant API responses
- `content/views.py`'s `_filter_sessions_for_participant` (or `session_list`/`session_today`, whichever is the actual entry point) should return NO sessions at all (empty list) for a waitlisted participant — same as how future weeks currently return nothing, just extended to also cover "hasn't started yet at all."
- Add a `is_waitlisted` boolean and the cohort's `program_start_date` (if known) to whatever response the mobile app uses to determine what to show on Home/Courses — check `participants/views.py`'s `profile` endpoint (`GET /api/profile/`) as the likely place, since that's probably already fetched by the app and is a natural place to surface this. Add `is_waitlisted` and `program_start_date` (nullable, ISO date string, null if no `CohortStartDate` exists yet for their cohort) to that response.

### 5. Mobile: show a waitlist message
On the Home screen (`HomeScreen.js`) — check the participant's profile response for `is_waitlisted`. If `true`, replace the normal "Today's Session" card with a simple message card, e.g.: **"Your program starts on [formatted program_start_date]"** (or a generic "Your program start date will be announced soon" if `program_start_date` is null, meaning the admin hasn't set one yet for their cohort). The Courses tab should also reflect this — showing an empty state with the same waitlist message rather than an empty/broken-looking session list.

## What NOT to change
- Do NOT change `enrolled_at` semantics or how/when it's set — stays exactly as "signup timestamp," untouched.
- Do NOT change the actual unlocking math (calendar-day gating, week-to-week 7-day + full-completion gate, sequential-read-in-order requirement, session overrides) — only change WHICH date those calculations anchor to (cohort start date instead of individual enrollment date).
- Do NOT retroactively change behavior for existing participants whose cohort has no `CohortStartDate` set yet — per the waitlist logic above, they should simply show as waitlisted (with a generic "start date coming soon" message) until an admin sets one, not error out or behave unpredictably.
- Do NOT build anything for cross-cohort scheduling, multiple start dates per cohort, or cohort start date editing history — one current start date per cohort is sufficient for this task.

## Testing expectations
- Create a `CohortStartDate` for cohort 1 with `program_start_date` a few days in the FUTURE — confirm a participant in cohort 1 (regardless of their own `enrolled_at`) shows `is_waitlisted: true`, sees no sessions, and the app displays the "program starts on [date]" message.
- Update that `CohortStartDate` to a date in the PAST (or today) — confirm the same participant now correctly sees Week 1 Day 1 unlocked (using the existing day/sequential gating logic), with Day 0 anchored to `program_start_date`, not their individual `enrolled_at`.
- Test two participants in the same cohort with DIFFERENT `enrolled_at` values (e.g., one signed up a week before the other) — confirm both see IDENTICAL content unlock status once the cohort start date has passed, proving individual signup timing no longer matters once the cohort has started.
- Test a participant whose cohort has NO `CohortStartDate` row at all — confirm they show as waitlisted with the generic "coming soon" message, not an error.
- Confirm cohort targeting (`group1/2/3`), session overrides, and sequential-day-completion logic all still compose correctly on top of the new cohort-anchored dates — re-run a couple of the existing verified scenarios from earlier scheduling tasks with a past `CohortStartDate` set, confirming nothing regressed.
- Run `python manage.py check` and confirm the new migration applies cleanly.
