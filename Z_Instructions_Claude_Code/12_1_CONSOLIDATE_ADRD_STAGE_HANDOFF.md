# WECARE 3.0 — Consolidate ADRD Stage Field + Rename Import Mapping Labels

## Context
The participant import feature (CSV/Excel, `backend/participants/admin.py`) currently has TWO separate mappable fields that represent overlapping concepts:
- `group2` (existing model field, choices: mild/moderate/severe, defaults to "moderate" if not set during import)
- `adrd_stage` (newer model field, added in a recent task, also intended to represent ADRD severity/stage)

**Root cause of the reported issue:** if an admin maps only "ADRD Stage" (→ `adrd_stage`) during import but leaves "Condition Group (mild/moderate/severe)" (→ `group2`) unmapped, the `adrd_stage` field gets the correct imported value, but `group2` silently defaults to `"moderate"` (per the existing default-fallback logic in the row-import loop). Since `group2` is what's actually displayed/used elsewhere (e.g., participant list `list_display`, filtering), it LOOKS like the import "isn't working" even though `adrd_stage` was actually set correctly — they're just two different fields, and only one is visible/relied-upon in practice.

**Stakeholder decision: consolidate to ONE field.** Remove `adrd_stage` from the import mapping entirely, keep only `group2`, and rename it for clarity so admins understand what it represents.

## Requirement

### 1. Remove `adrd_stage` as a separate importable/mappable field
In `backend/participants/admin.py`:
- Remove `'adrd_stage': 'ADRD Stage'` from the `field_map` dict shown on the preview screen.
- Remove the `adrd_stage` entry from the `mapping` dict built in the import POST handler (the dict that reads `request.POST.get('map_adrd_stage', ...)`).
- Remove the line in the row-import loop that sets `p.adrd_stage = row.get(mapping['adrd_stage'], ...)`.
- In `csv_preview.html`, remove the corresponding `<div class="map-row">` block for ADRD Stage (the one with `name="map_adrd_stage"`).

**Do NOT remove the `adrd_stage` model field itself** from `Participant` (`backend/participants/models.py`) — it may still be referenced elsewhere (e.g., the participant stats page, admin fieldsets from a previous task). This task only removes it from the CSV/Excel import mapping flow, not from the model or other parts of the admin. If you find it's actively displayed/edited elsewhere (e.g., a "Recruitment Cohort" or clinical-info fieldset on the participant change form), leave that alone — flag it in your summary as still existing but now orphaned from bulk import, and note that as a decision point for the stakeholder to revisit later if they want it removed entirely from the system.

### 2. Merge ADRD-stage-related synonyms into `group2`'s synonym list
In the `FIELD_SYNONYMS` dict (added in the previous Excel-import task), merge the synonyms that were previously listed under `adrd_stage` (things like "ADRD Stage", "Stage", "Disease Stage") into `group2`'s synonym list, so a column literally named "ADRD Stage" in an uploaded file now correctly auto-maps to `group2` instead of (the now-removed) `adrd_stage`. Remove the `adrd_stage` entry from `FIELD_SYNONYMS` entirely.

### 3. Rename field labels shown on the mapping/preview screen
Update the `field_map` dict values (the human-readable labels shown next to each dropdown) as follows:
- `group1`: `'Study Cohort (intervention/control)'` → `'Group1 - Study Cohort (Intervention/Control)'`
- `group2`: `'Condition Group (mild/moderate/severe)'` → `'Group2 - ADRD Stage (Mild/Moderate/Severe)'`
- `group3`: `'Stress Group (high/low)'` → `'Group3 - Stress Group (High/Low Stress)'`
- `relationship` (maps to `adrd_relationship_group`): `'Care Relationship'` → `'Care Relationship/ADRD relationship group - Spouse, Children/Adult Child, Other Relative'`

Leave all other labels (`email`, `first_name`, `last_name`, `label`, `gender`, `age`, `cohort`) exactly as they currently are — not part of this rename.

## What NOT to change
- Do NOT remove or rename the `Participant.adrd_stage` model field itself — only remove it from the import/mapping flow, per the note in section 1.
- Do NOT change the actual choices/values for `group1`, `group2`, `group3` (still intervention/control, mild/moderate/severe, high/low respectively) — only the display LABEL on the import mapping screen changes, not the underlying field choices or model.
- Do NOT change the `cohort` field or its label — that's a separate, already-correct concept (recruitment wave, not clinical severity) and shouldn't be touched by this task.
- Do NOT change anything about the auto-mapping normalization logic (`_normalize_header`, `compute_auto_mapping`) itself — just update which synonym list `adrd_stage`'s old synonyms feed into.

## Testing expectations
- Upload a test file with a column named "ADRD Stage" containing values like "mild"/"severe" — confirm it now auto-maps to the "Group2 - ADRD Stage (Mild/Moderate/Severe)" dropdown (not a now-nonexistent adrd_stage option), and after import, `participant.group2` is set correctly (not defaulted to "moderate").
- Confirm the mapping screen no longer shows a separate "ADRD Stage" dropdown alongside "Group2 - ADRD Stage" — only one exists now.
- Confirm the three renamed labels (Group1, Group2, Group3) and the relationship label display correctly with the new text on the preview screen.
- Confirm a full import still works end-to-end with the renamed/consolidated fields, producing correct `group1`/`group2`/`group3`/`adrd_relationship_group` values on created participants.
- Run `python manage.py check` to confirm no errors from removing the `adrd_stage` import-mapping code paths.
