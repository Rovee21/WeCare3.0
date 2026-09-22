# WECARE 3.0 — Session Targeting by Relationship Type

## Context
`Session` model (`backend/content/models.py`) currently supports targeting by three dimensions: `target_group1` (Intervention/Control), `target_group2` (Mild/Moderate/Severe), `target_group3` (High/Low Stress) — each optional, blank meaning "applies to everyone regardless of that dimension" (established convention, see `_filter_sessions_for_participant` in `backend/content/views.py`).

`Participant` model has `adrd_relationship_group` with existing choices: `spouse` (Spouse), `children` (Children / Adult Child), `relative` (Other Relative) — this field already exists and is populated at enrollment/via CSV import, but is NOT currently used for session content targeting, only stored as participant metadata.

**New requirement:** add relationship type as a FOURTH session-targeting dimension, following the exact same pattern as `target_group1/2/3` — e.g., a session could be targeted specifically at spouse caregivers only, or left open to all relationship types.

## Requirement

### 1. Add `target_relationship` field to `Session`
In `backend/content/models.py`, add to the `Session` model, following the exact same style/pattern as the existing `target_group1/2/3` fields (including the dropdown choices approach with blank="All" that was specifically added earlier to prevent case-mismatch admin errors):
```python
target_relationship = models.CharField(
    max_length=20, blank=True,
    choices=[('', 'All'), ('spouse', 'Spouse'), ('children', 'Children / Adult Child'), ('relative', 'Other Relative')]
)
```
Match the exact choice VALUES used on `Participant.adrd_relationship_group` (`spouse`/`children`/`relative`) so filtering comparisons work directly without any translation layer. Requires a migration.

### 2. Wire into cohort-targeting filter logic
In `backend/content/views.py`'s `_filter_sessions_for_participant`, add the same blank-means-any matching logic already used for `target_group1/2/3`, now also checking `target_relationship` against the participant's `adrd_relationship_group`. This should compose correctly alongside all existing targeting/gating logic (cohort start date, day/week unlocking, sequential completion, session overrides) — it's simply one more AND condition in the existing cohort-match check, not a replacement for any of the existing logic.

### 3. Add to Django Admin — Session edit form and list
- Add `target_relationship` to `SessionAdmin`'s cohort-targeting fieldset, alongside the existing group1/2/3 fields.
- Add a new column to `SessionAdmin.list_display`, following the exact same style as the just-added Group 1/2/3 columns from the previous round of work — e.g., labeled `Relationship Target` or similar, displaying `get_target_relationship_display()` (blank → "All", matching the existing pattern).

### 4. Do NOT touch CSV/Excel import
Check `FIELD_SYNONYMS` and `field_map` in `backend/participants/admin.py` — this is for PARTICIPANT import (setting `adrd_relationship_group` on a participant), which is a DIFFERENT concept from SESSION targeting being added in this task. Do NOT confuse the two. No changes needed to CSV import for this task — that already correctly imports `adrd_relationship_group` on participants; this task is only about SESSION-level targeting, a separate admin form (`SessionAdmin`, not `ParticipantAdmin`).

## What NOT to change
- Do NOT change `Participant.adrd_relationship_group` or its choices — unchanged, this task only reads/matches against it.
- Do NOT change `target_group1`/`target_group2`/`target_group3` or their logic — this adds a fourth, independent targeting dimension alongside them, not a replacement.
- Do NOT change any other gating logic (cohort start dates, day/week unlocking, sequential completion, session overrides) — this composes with all of that unchanged.
- Do NOT change the participant CSV/Excel import feature — unrelated to this task.

## Testing expectations
- Create a session with `target_relationship='spouse'` and leave group1/2/3 blank — confirm a participant with `adrd_relationship_group='spouse'` sees it, while a participant with `adrd_relationship_group='children'` does NOT.
- Create a session with `target_relationship` left blank ("All") — confirm participants of any relationship type see it (assuming other targeting dimensions also match/are blank).
- Confirm combining `target_relationship` with existing `target_group1/2/3` targeting works correctly (e.g., a session targeted at BOTH `group1='intervention'` AND `target_relationship='spouse'` should only show for participants matching both).
- Confirm the new admin list column and edit-form field work correctly.
- Run `python manage.py check` and confirm the migration applies cleanly.
