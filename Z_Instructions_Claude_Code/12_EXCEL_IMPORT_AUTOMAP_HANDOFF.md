# WECARE 3.0 — Excel Upload Support + Smarter Auto-Mapping for Participant Import

## Context
The participant bulk-import feature currently only accepts CSV files (`backend/participants/admin.py`'s `csv_import_view`, plus `backend/templates/admin/participants/csv_upload.html` and `csv_preview.html`). It already has a column-mapping UI: after upload, the admin sees a preview screen where they manually select which uploaded column maps to which `Participant` field (email, first_name, last_name, label, gender, age, relationship, group1, group2, group3, adrd_stage, cohort — the last one was just added in a previous task).

Currently, `field_map` (shown on the preview screen) does a very basic case-insensitive exact-match pre-selection:
```python
{% if h|lower == field_key|lower %}selected{% endif %}
```
in `csv_preview.html` — this only auto-selects a dropdown option if the CSV header text is IDENTICAL (case-insensitive) to the internal field key (e.g., a column literally named "email" matches `email`), which rarely happens with real-world survey exports using different naming conventions.

## Requirement

### 1. Add Excel (.xlsx) upload support
The upload page (`csv_upload.html`) and the `csv_import_view` POST handler currently only accept `.csv` files (`request.FILES['csv_file']`, parsed via Python's `csv.DictReader`). Extend this to also accept `.xlsx` files:
- Update the file input's `accept` attribute in `csv_upload.html` to include `.xlsx` alongside `.csv` (e.g., `accept=".csv,.xlsx"`)
- In the view, detect the file type by extension (or content-type) and parse accordingly:
  - `.csv` → keep using `csv.DictReader` exactly as now
  - `.xlsx` → use `openpyxl` to read the first sheet, treating the first row as headers, converting each subsequent row into a dict keyed by those headers (matching the same shape `csv.DictReader` produces, so all downstream code — preview rendering, row-import logic — works identically regardless of which format was uploaded)
- Add `openpyxl` to `backend/requirements.txt` if not already present (check first — it's likely already there since the `xlsx` skill/other tooling may use it, but confirm).
- Update the upload page's hint text to mention both formats are accepted.
- Update variable/field naming from `csv_file`/`csv_data`/`decoded` etc. to be format-agnostic where it makes sense for clarity (e.g., rename internally to something like `import_file` if easy, but don't do a large disruptive rename — prioritize correctness over cosmetic renaming; existing variable names are fine to keep if renaming would touch too much).

### 2. Smarter auto-mapping (fuzzy/synonym matching)
Replace the current exact-match-only pre-selection with a more forgiving matching system. For each internal field, define a list of common synonym/variant column names that should auto-match, e.g.:
- `email` → matches columns named "Email", "Email Address", "E-mail", "EmailAddress", "Q_Email", etc.
- `first_name` → matches "First Name", "FirstName", "First", "Given Name", etc.
- `last_name` → matches "Last Name", "LastName", "Last", "Surname", "Family Name", etc.
- `gender` → matches "Gender", "Sex"
- `age` → matches "Age", "Participant Age"
- `relationship` → matches "Relationship", "Care Relationship", "Relationship to Care Recipient", "ADRD Relationship"
- `group1` → matches "Group1", "Group 1", "Study Cohort", "Intervention Group", "Cohort Assignment" (careful: don't confuse with the NEW `cohort` field below — these are different concepts, see note)
- `group2` → matches "Group2", "Group 2", "Condition Group", "Severity"
- `group3` → matches "Group3", "Group 3", "Stress Group"
- `adrd_stage` → matches "ADRD Stage", "Stage", "Disease Stage"
- `cohort` → matches "Cohort", "Recruitment Cohort", "Recruitment Wave", "Cohort Number" (this is the recruitment-wave field added in the previous task — keep it clearly distinguished from group1/2/3 in the synonym lists, same as it's distinguished elsewhere in the codebase)
- `label` → matches "Label", "Display Name", "Nickname"

**Matching approach:** normalize both the CSV/Excel header and the synonym list entries the same way before comparing — e.g., lowercase, strip whitespace, remove punctuation/underscores/hyphens (so "E-mail", "e_mail", and "Email" all normalize to the same comparable string: "email"). Use Python's stdlib (`re`, `str` methods) for this — no need for a fuzzy-matching library like `fuzzywuzzy`, exact-after-normalization matching against a reasonable synonym list will cover the realistic cases well without adding a new dependency.

Where to add this: put the synonym mapping as a dict constant near the top of `backend/participants/admin.py` (or in a small new module if that's cleaner — your call), and use it in the preview-rendering logic to determine which dropdown option gets `selected` for each field, replacing the current bare `h|lower == field_key|lower` check. You'll likely need to pass a pre-computed "best guess" mapping from the view into the template context (e.g., a dict of `{field_key: matched_header_or_none}`) rather than trying to do fuzzy matching inside the Django template itself (templates are the wrong place for this logic).

**Still keep it editable:** the auto-match is just a smarter *default selection* — the admin can still override any dropdown manually before clicking Import, exactly as today. Don't remove the ability to manually correct a wrong guess.

## What NOT to change
- Do NOT change the actual field list being mapped (email, first_name, last_name, label, gender, age, relationship, group1, group2, group3, adrd_stage, cohort) — just add Excel support and smarter matching for these existing fields.
- Do NOT add a fuzzy-matching library dependency (like `fuzzywuzzy`/`rapidfuzz`) — normalization + exact match against a synonym list is sufficient and keeps things simple.
- Do NOT change the actual participant-creation logic (the loop that builds `Participant` objects from mapped rows) — that logic works the same regardless of source format or how the mapping was pre-selected, since by the time it runs, the admin has confirmed/submitted a mapping either way.
- Do NOT change the CSV path's behavior for anyone who's already used it before this change — a plain CSV upload should still work exactly as it did, just now with smarter pre-selected mapping defaults.

## Testing expectations
- Upload a `.csv` file with cleanly-named headers matching the synonym list (e.g., "Email Address", "First Name", "Last Name") — confirm the preview screen auto-selects the correct dropdown for each, without the admin needing to manually pick anything.
- Upload the same data as an `.xlsx` file instead — confirm identical behavior (same preview, same auto-mapping, same successful import) to prove format-parity.
- Upload a file with a column name NOT in any synonym list (e.g., "Contact Info") — confirm it correctly falls back to "— skip —" (no incorrect guess), and the admin can still manually map it if needed.
- Upload a file with intentionally ambiguous/messy headers (e.g., "E-MAIL", " first_name ", "Last-Name") — confirm normalization handles whitespace/punctuation/case correctly and still auto-matches.
- Confirm a full end-to-end import (both CSV and XLSX) still successfully creates participants with correct field values, same as the existing (already-verified) CSV import flow.
- Run `python manage.py check` to confirm no import/syntax errors from the `openpyxl` addition.
