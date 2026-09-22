# WECARE 3.0 — Cohort (Recruitment Area) Field

## Context
`Participant` model (`backend/participants/models.py`) currently has `group1` (Intervention/Control), `group2` (Mild/Moderate/Severe), `group3` (High/Low Stress) — these represent clinical/study-design groupings, unrelated to what's being added here.

**New, separate concept:** a "Cohort" field representing which **recruitment area/wave** a participant belongs to — e.g., "Cohort 1", "Cohort 2", etc. This is about *when/where* they were recruited into the year-long study, completely independent of their group1/group2/group3 assignments. A participant in Cohort 1 could be in any combination of group1/group2/group3, same for Cohort 2, etc. — no relationship between cohort number and the existing groups.

Per stakeholder: only one cohort is "active" for new recruitment at a time (e.g., you're currently only recruiting Cohort 1 participants), but the field itself is just a label on each participant — doesn't need to enforce "only one active cohort" as a system constraint for this task, just needs to store which cohort each participant belongs to.

## Requirement

### 1. Add a `cohort` field to `Participant`
Add to `backend/participants/models.py`:
```python
cohort = models.PositiveSmallIntegerField(default=1, help_text="Recruitment cohort/wave number (e.g., 1 = Cohort 1, 2 = Cohort 2). Represents which recruitment area/wave the participant belongs to — independent of group1/group2/group3.")
```
Use a simple integer (not a CharField with choices) since cohort numbers will keep incrementing over the year-long study (Cohort 1, 2, 3...) with no fixed upper bound — a free-form positive integer is more appropriate than a fixed choices list that would need editing every time a new cohort starts.

Requires a migration — run `makemigrations` / `migrate` as normal.

### 2. Add to Django Admin
In `backend/participants/admin.py`:
- Add `cohort` to `ParticipantAdmin.list_display` so it's visible in the participant list table (check current `list_display` — likely lists things like `participant_id`, `email`, `language`, `group1`, `group2`, `group3`, `is_enrolled`, etc.; add `cohort` in a sensible position, probably near the other group fields)
- Add `cohort` to `list_filter` so admins can filter the participant list by cohort — this will be genuinely useful for a year-long study with a growing number of cohorts
- Add `cohort` as an editable field in whatever fieldset currently holds `group1`/`group2`/`group3` on the participant change form (check current fieldsets — there's likely a "Cohort Assignment" or similar section; either add `cohort` there with a clarifying note that it's a different concept, or create a small new fieldset specifically for it to avoid confusion between "cohort" (recruitment wave) and "group1/2/3" (clinical study groups) — use your judgment on which is clearer, but the distinction should be visually/organizationally clear to an admin user, not just via help text)

### 3. Add to CSV import
The CSV import feature (`csv_import_view`, `backend/participants/admin.py`) currently maps CSV columns to fields including `group1`, `group2`, `group3`, `adrd_stage`, etc. (check the current `field_map` dict in the preview context and the field-extraction logic in the import POST handler). Add `cohort` as a mappable field:
- Add `'cohort': 'Cohort / Recruitment Wave'` to the `field_map` dict shown on the mapping/preview screen
- In the actual row-import logic, extract and set `cohort` from the mapped column, parsing it as an integer (default to `1` if the column is blank/unmapped/unparseable — don't fail the whole row import over a missing cohort value, just fall back to the default)

### 4. Add to CSV import spreadsheet template/example (if one exists)
Check if there's an example CSV or documented expected-columns list anywhere (e.g., in the upload page's hint text `backend/templates/admin/participants/csv_upload.html`) — if so, add "Cohort" to that list of expected fields for consistency, matching the style of existing entries there.

## What NOT to change
- Do NOT touch `group1`, `group2`, `group3`, or `adrd_stage` — those are unrelated, unchanged clinical grouping fields.
- Do NOT add any "only one active cohort" enforcement logic (e.g., preventing new enrollments into old cohorts, or auto-incrementing based on some global "current cohort" setting) — out of scope for this task. Just a plain field on each participant, editable freely by admins.
- Do NOT change the mobile app — cohort is purely an admin/research-tracking concept, not something participants see or interact with.
- Do NOT change the enrollment (`/api/enroll/`) flow or its response shape — cohort isn't part of what's returned to the app.

## Testing expectations
- Confirm the migration applies cleanly (`python manage.py check`, `makemigrations --check --dry-run` afterward should show no pending changes).
- Confirm existing participants default to `cohort=1` after migration (check a few existing participants in Django shell).
- Confirm `cohort` is visible and filterable in the Django Admin participant list.
- Confirm `cohort` is editable on the participant detail/change page.
- Test CSV import: upload a test CSV with a "Cohort" column containing values like `1`, `2`, blank for one row — confirm imported participants get the correct cohort numbers, and the blank one defaults to `1` without erroring out the whole import.
