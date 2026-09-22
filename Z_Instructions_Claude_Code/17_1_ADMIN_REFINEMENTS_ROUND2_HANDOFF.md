# WECARE 3.0 — Admin Refinements Round 2

## Context
Building on the just-completed bug-fix batch (session status tracking, count fixes, back buttons on 6 pages, enrollment code column, latest emotion fix). This is a follow-up refinement pass based on live testing of that batch.

## Requirement

### 1. Back button placement — reduce to single position on two specific pages
On `http://localhost:8000/admin/participants/cohortstartdate/` and `http://localhost:8000/admin/content/dailynotificationsettings/1/change/` ONLY — the back button from the previous task currently appears at BOTH top and bottom. Change these two specific pages to show it in only ONE position (your choice of top-only or bottom-only, whichever is simpler given the current template structure for these two pages — no strong preference from stakeholder). All other pages from the previous task (participant change form, session list, session change form, engagement log list) should KEEP both top and bottom placement, unchanged — this reduction applies ONLY to these two pages.

### 2. Stricter completion criteria for session "Completed" status
**Current behavior (from the just-completed batch):** a session is marked `is_read=True`/"Completed" if the participant spends more than 3 seconds total on the session screen (any tab), regardless of which tabs they actually engaged with.

**New required behavior:** a session should only be marked "Completed" if BOTH of the following are true:
- The participant has spent at least **60 seconds on the Video tab** (i.e., `video_time_seconds >= 60` OR — if more precise — `video_watch_seconds >= 60`, meaning actual playback time rather than just tab-dwell time; use `video_watch_seconds` since it's the more meaningful signal per its own original design intent from the task that introduced it) AND has actually engaged with playback in some form (this is inherently covered if `video_watch_seconds >= 60`, since that field only increments during actual playback).
- The participant has spent at least **60 seconds on the Text tab** (`text_time_seconds >= 60`).

**Where to implement this check:** likely in the same place the "in progress → completed" transition currently happens (the unmount cleanup logic in `DailySessionScreen.js` that currently checks `total > 3 seconds` before calling `markAsRead`, per the just-completed batch's summary) — replace that simple 3-second-total threshold with the new dual 60-second-per-tab requirement. If a session has no video (text-only, or vice versa, if any such sessions exist or could exist) — decide sensible fallback behavior: if a session genuinely has no video content (`video_url` is empty), don't require the video threshold to be met for that specific session, only the tabs that actually exist/have content should need to meet their respective threshold. Check current session data model for how to detect "does this session actually have a video" vs "does it have text" before assuming both are always present.

**Where the actual `markAsRead` call happens** — reconfirm this is still triggered from the same unmount cleanup point as before, just with the new threshold logic gating whether it fires, rather than the old simple total-time check.

### 3. Session admin list — restructure columns
On `http://localhost:8000/admin/content/session/`, update `SessionAdmin.list_display`:

**Remove these existing columns:**
- `# Read` (the read-count column)
- `Video` (has-video checkbox/indicator column)
- `Text` (has-text checkbox/indicator column)

(Per stakeholder: virtually all sessions have both video and text by default, so these indicator columns provide little value; read-count is being removed from this view specifically, though the underlying data/metric itself is NOT being deleted anywhere else — this is purely a display change on this one list page.)

**Rename this existing column:**
- `Cohort Target` → `Group 1 (Intervention/Control)` (displaying the session's `target_group1` value)

**Add these new columns:**
- `Group 2 (Mild/Moderate/Severe)` — displaying the session's `target_group2` value
- `Group 3 (High/Low Stress)` — displaying the session's `target_group3` value

**Resulting column order** (suggested, adjust if a different order makes more sense given the admin's existing method-based column implementations): Week number, Day number, Title, Group 1 (Intervention/Control), Group 2 (Mild/Moderate/Severe), Group 3 (High/Low Stress), Is active.

Check `SessionAdmin`'s existing `has_video`/`has_text`/`cohort_target`/`participants_read` methods (or however these are currently implemented — likely custom methods given the naming pattern seen elsewhere in this admin) — remove the ones no longer needed, add new simple methods (or just reference the model fields directly in `list_display` if Django allows direct field references for `target_group2`/`target_group3`, which it should since they're plain model fields, not computed values) for the two new columns.

### 4. Add back buttons to two more pages
Extend the back-button feature from the previous task (reusable `templates/admin/_back_button.html` include) to these two additional pages, with BOTH top and bottom placement (standard placement, same as most pages from the previous task — NOT the reduced single-placement treatment from requirement #1 above, which only applies to the two pages named there):
- `http://localhost:8000/admin/content/notificationlog/`
- `http://localhost:8000/admin/participants/participant/`

Follow the exact same implementation pattern already established in the previous task for the other list-page back buttons (check how it was done for `engagementlog`'s list page specifically, since that's the most directly comparable existing example — a list view, not a change-form view).

## What NOT to change
- Do NOT change back-button placement on any pages other than the two named in requirement #1 — all others keep their existing top+bottom placement from the previous task.
- Do NOT remove or alter the underlying `video_time_seconds`, `video_watch_seconds`, `text_time_seconds` tracking logic itself — only the THRESHOLD used to decide "completed" status changes, not how those values are measured/accumulated.
- Do NOT change anything about the "in progress" state or its trigger (`mark_in_progress`/`started_at`) — only the "completed" transition's criteria are being tightened.
- Do NOT remove `target_group1`/`target_group2`/`target_group3` fields or their underlying cohort-targeting logic (session filtering by group) — this task only changes how they're LABELED and DISPLAYED in the admin list view, not how they function.
- Do NOT change the participant stats page's own read/completion display — only the main `/admin/content/session/` list page's columns are being restructured per requirement #3.

## Testing expectations
- Confirm `cohortstartdate` list page and `dailynotificationsettings` change form each show the back button in exactly ONE position (top or bottom, not both) — all other admin pages from the previous task unaffected.
- Open a session with both video and text content. Watch less than 60 seconds of video AND less than 60 seconds on text, leave — confirm status remains "In Progress," NOT "Completed."
- Watch 60+ seconds of video but spend less than 60 seconds on text, leave — confirm still "In Progress" (both thresholds required).
- Meet both thresholds (60+ seconds video watch time AND 60+ seconds on text tab) — confirm status correctly transitions to "Completed."
- If a text-only or video-only session exists (or can be created for testing) — confirm the fallback logic doesn't incorrectly block completion for content that doesn't exist on that particular session.
- Confirm `/admin/content/session/` list page shows the new column set (Week, Day, Title, Group 1, Group 2, Group 3, Is active) with correct values pulled from `target_group1`/`target_group2`/`target_group3`, and that `# Read`/`Video`/`Text` columns are gone.
- Confirm back buttons now appear (top + bottom) on `notificationlog` list and `participant` list pages.
- Run `python manage.py check`.
