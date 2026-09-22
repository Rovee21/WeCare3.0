# Platform Testing Notes — Task Tracker

Source: `Platform Testing Notes and Observations.docx`. Tracking fixes here, checked off as completed.

## Tier 1 — Quick Wins

- [x] Make Participant's "Group 2" field optional (blocks profile creation when unknown at enrollment)
- [x] Make Group 1, Group 3, and Caregiver Relationship also optional (only email is mandatory); add first/last name/label as enterable admin fields (not shown in the list view); warn (non-blocking) if a participant's cohort has started but details are still missing; block clearing an already-filled baseline field once the cohort has started; block setting a cohort's start date to today/past while any of its participants are still incomplete
- [x] Add a visible "Download CSV template" link on the import page (built as an Excel template with all fields, Email highlighted as mandatory, one example row); reorganized the Participant changelist buttons (all 4 right-aligned, two rows); fixed CSV import to leave unmapped baseline fields blank (no more silent defaulting) and show the same "cohort started but incomplete" warning as manual add; guarded against importing the template's own example row
- [x] Reorganize Session admin fields so English/Chinese content are visually grouped/separated — split into 6 headed sections (English Video, English Text/Word Doc, English Text/PDF Alternative, and the same 3 for Chinese) with real visual gaps between Word-doc and PDF groups, and distinct header background colors (blue for English, purple for Chinese); reworded upload labels for clarity ("for text section", bold "Optional", explicit "leave empty if using the Word document instead" note)
- [x] Add a descriptive name/label to cohorts (numeric-only today) — added `CohortStartDate.label`, shown in its list view and in a new "Cohort Label" column on the Participant list; changed Participant's cohort field from a bare number spinner to a dropdown showing "Cohort N — Label" (with a "Not yet assigned" option, cohort is now nullable); cohort dates now display as "2026-Sep-13" everywhere shown. Fixed CSV/Excel import: invalid Group1/2/3/Relationship values (e.g. "superb") are left blank with a warning instead of stored as garbage (verified against a real .xlsx file, not just CSV); an unconfigured cohort number is now left unassigned (not silently saved) with a warning telling the admin to create that cohort first. Removed Participant "Label" from the admin form and CSV/Excel import/template (model field kept for the still-pending mobile display-name fix, just hidden here) — not the same thing as the new Cohort Label above
- [ ] Show current week / cohort-start-date info directly on the Participant admin page
- [ ] Truncate the OS notification preview text (full message still viewable in-app)
- [ ] Fix blank participant profile name after login

## Tier 2 — Medium Effort (needs investigation first)

- [ ] Wire up the "Larger Text" accessibility toggle — currently has no effect
- [ ] Fix PDF upload failing on OneDrive-sourced files
- [ ] Investigate sessions 4.1/4.2 not reflecting edits / uploaded content "disappearing" (leading theory: week/day collision — both were set to Week 1 Day 1 during testing)
- [ ] Investigate "6 courses shown, only 1 accessible" mismatch on the home page
- [ ] Fix in-app content rendering: lost text formatting, missing images, non-clickable emoji/comment buttons
- [ ] Fix Voice Journal playback of past recordings
- [ ] Add a bulk "assign cohort" admin action (avoid editing participants one by one)
- [ ] Verify "previously delivered courses stay accessible" behavior — confirm existing logic is correct, fix if not

## Tier 3 — Bigger Tasks / Product Decisions Needed

- [ ] Delayed/individual start-date support ("Week 0" / late-joiner scenario) — needs a real design, not just a bug fix
- [ ] In-app notification history/center
- [ ] Unread badge count on the app icon
- [ ] Admin content preview (see a session as a participant would, before publishing)
- [ ] Cohort duration / end-of-program handling (what happens after week 7)
- [ ] General performance investigation (admin + app load times)
- [ ] Daily notifications auto-reflect the day's session title instead of a fixed generic message
- [ ] Notification delivery delay (~2+ min) — may be inherent to trigger infrastructure, needs discussion
- [ ] "Calendar history view" / app feels outdated — likely just needs a fresh TestFlight build with everything already fixed this session

## Deferred / Separately Tracked

- [ ] Enrollment-code email sending — Gmail SMTP auth failing (`535-5.7.8 BadCredentials`), on hold per user
