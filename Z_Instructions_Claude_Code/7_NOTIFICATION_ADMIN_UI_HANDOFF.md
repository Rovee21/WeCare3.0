# WECARE 3.0 — Notification Admin UI

## Context
This is the final piece connecting all previously built notification infrastructure into an actual user-facing Django Admin interface. Everything below already exists and is verified working:

- `backend/participants/notifications.py`:
  - `send_and_log_notification(participant, title, body, notification_type=None)` — immediate send + log.
  - `send_and_log_notification_bulk(participants, title, body, notification_type=None)` — immediate bulk send + log.
  - `schedule_notification(participant, title, body, scheduled_for, notification_type=None)` — creates a pending row for future send (or delegates to immediate send if `scheduled_for` is None/past).
  - `schedule_notification_bulk(participants, title, body, scheduled_for, notification_type=None)` — bulk version.
- `NotificationLog` model (`backend/content/models.py`) has: `participant`, `notification_type` (includes `TYPE_MANUAL`), `title`, `push_up` (body), `status` (`pending`/`sent`/`failed`/`skipped_no_token`), `scheduled_for`, `sent_at` (creation timestamp), `actually_sent_at`, `opened_at`.
- `Participant` model has `group1`, `group2`, `group3` (cohort fields, already used elsewhere for content targeting — check `content/views.py`'s `_filter_sessions_for_participant` for the existing pattern/choices used for these three fields, to stay consistent).
- Existing custom Django Admin pages exist as a reference pattern: the participant stats page (`backend/participants/admin.py`'s `stats_view`, rendering `backend/templates/admin/participant_stats.html`) and the CSV import flow (`csv_import_view`, `backend/templates/admin/participants/csv_upload.html` and `csv_preview.html`). Follow similar conventions/styling for consistency (dark theme styling used in those templates, `TemplateResponse`, custom `get_urls()` additions on `ParticipantAdmin`, etc.).

## Requirement

Build BOTH of the following, per stakeholder decision (not choosing one over the other):

### 1. A custom "Send Notification" admin page
A new page, e.g. at `/admin/participants/participant/send-notification/`, added via `get_urls()` on `ParticipantAdmin` (same pattern as `stats_view` and `csv_import_view`). Should have a "Send Notification" button/link accessible from the participant list page (similar to how "Import CSV" got a button — check `changelist_view` override and `change_list.html` template override for that existing pattern).

The page should let the admin:
- **Choose a target type:**
  - Single participant (searchable/select dropdown)
  - A cohort — meaning ANY of group1, group2, or group3 individually, or a combination (decide a reasonable UI for this — e.g., three optional dropdowns for group1/group2/group3, where leaving one blank means "any value for that dimension," matching the same "blank = universal" pattern already used for `Session.target_group1/2/3` cohort targeting elsewhere in the codebase — stay consistent with that existing convention)
  - Everyone (all participants)
- **Write a title and body** (freeform text, as already decided)
- **Choose send timing:**
  - "Send now" (immediate) — calls `send_and_log_notification` / `send_and_log_notification_bulk` depending on target type
  - "Schedule for later" — shows a datetime picker, calls `schedule_notification` / `schedule_notification_bulk` with that datetime
- **On submit:** actually perform the send/schedule, then show a clear success message summarizing the outcome (e.g., "Sent to 12 participants (2 skipped — no device token)" or "Scheduled for Aug 10, 2:00 PM — will send to 15 participants when processed").

Resolving "cohort" target to an actual list of `Participant` objects: filter `Participant.objects.all()` by whichever group1/2/3 values were selected (only filtering on dimensions the admin actually specified; blank/unset dimensions match everyone, consistent with how `Session` cohort targeting already works).

### 2. A Django Admin action on the Participant list
Add an admin `action` (the same mechanism `generate_code_only` and `generate_and_email_code` already use — check those in `ParticipantAdmin.actions` for the existing pattern) called something like `send_notification_to_selected`.

- Admin selects one or more participants via checkboxes on the participant list page (standard Django admin action selection UI — already used for the existing code-generation actions).
- Choosing "Send Notification" from the actions dropdown should NOT immediately send anything (you can't collect a title/body/timing choice from a plain admin action easily) — instead, it should redirect to the SAME custom "Send Notification" page built in part 1, but pre-populate/pre-select the chosen participants as the target (e.g., via query params like `?participant_ids=1,5,7`, which the page reads and pre-fills a "specific participants" mode instead of the single-participant or cohort mode).

This means: the admin action is really just a convenient shortcut INTO the custom page, pre-loaded with a specific multi-participant selection — not a fully separate second implementation. Reuse the same page/form/sending logic for all three targeting paths (single, cohort, selected-via-action) rather than duplicating.

### Suggested target-type handling on the page
Given the above, the custom page effectively needs to support 4 target modes cleanly:
- Single participant (dropdown)
- Cohort (group1/2/3 filters)
- Everyone
- Specific pre-selected participants (from the list-page action; show these as a read-only confirmed list on the page, e.g., "Sending to: P00001, P00005, P00007" if arriving via the action)

Pick a clean UI approach (e.g., radio buttons for target mode, showing/hiding the relevant sub-form) — use your judgment on exact layout, following the existing dark-theme styling conventions from `participant_stats.html` / `csv_upload.html` / `csv_preview.html` for visual consistency.

## What NOT to build yet
- Do NOT build the automatic daily-reminder trigger logic (`TYPE_DAILY`/`TYPE_UNREAD`/`TYPE_VJ` automated sends) — that's the final, separate later task.
- Do NOT build any Celery/cron/EventBridge automation for `send_scheduled_notifications` — still manual-trigger only for now, unchanged from the previous task.
- Do NOT change the underlying `notifications.py` functions themselves unless you find a genuine bug — this task is purely the UI layer calling them correctly.

## Testing expectations
- Send an immediate notification to a single participant via the custom page — confirm it arrives on a physical device and a `NotificationLog` row is created correctly.
- Send an immediate notification to "everyone" — confirm the right number of rows are created (matching total participant count) with correct per-participant outcomes (sent vs. skipped_no_token).
- Send an immediate notification filtered by a specific group1/group2/group3 combination — confirm ONLY matching participants receive rows/sends, verify against `Participant.objects.filter(...)` with the same criteria run manually in shell to cross-check the count matches.
- Schedule a notification for a few minutes in the future via the custom page (any target mode) — confirm `NotificationLog` rows are created as `pending` with correct `scheduled_for`, nothing sends immediately, and running `send_scheduled_notifications` after the time passes correctly delivers and updates status (reuse the exact verification approach from the previous scheduling task).
- From the Participant list page: select 2-3 specific participants via checkboxes, run the "Send Notification" action, confirm it redirects to the custom page with those participants pre-selected/shown, then complete the form (title/body/send now) and confirm ONLY those selected participants receive the notification (not the whole participant list).
- Run `python manage.py check` and confirm everything renders without template errors.
