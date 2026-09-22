# WECARE 3.0 — Bug Fixes & Admin UX Improvements Batch

## Context
Several issues surfaced during live testing tonight. Grouping into real bugs (likely double-counting/premature status issues) vs. UX/copy improvements.

---

## BUG 1: Session marked "read" on open, not on actual completion

**Problem:** Opening a session in `DailySessionScreen.js` immediately calls `markAsRead(course.id)` on mount (check current `useEffect` in that file) — meaning just tapping into a session marks it fully "read" in the admin, even if the participant never opens the Text tab, never plays the video, and immediately navigates away.

**Fix:** Introduce a distinct "in progress" vs "read/completed" state.
- Check `ParticipantSession` model (`backend/content/models.py`) — likely just has `is_read` (boolean). Add a `status` field or similar with at least three states: e.g. `not_started` / `in_progress` / `completed` (or reuse `is_read` as the "completed" signal and add a separate boolean/timestamp for "opened but not completed" — your call on the cleanest schema, but the distinction needs to exist).
- **Decide what constitutes "completed"** — reasonable definition: the participant has spent a meaningful amount of time on the session (e.g., matches whatever threshold `logEngagement`'s cleanup function already uses, `secondsSpent > 3`, from the earlier engagement-tracking work) OR has visited multiple tabs OR has explicitly interacted (played video, viewed text). Given there's no explicit "mark as done" button in the current UI, the most practical approach: mark as "in_progress" the moment the session opens (replacing the current immediate `markAsRead` call), and mark as "completed"/"read" only when the participant actually leaves the screen (the existing `useEffect` cleanup function, which already fires `logEngagement`) — i.e., move the completion signal from mount-time to unmount-time, reusing the same engagement-tracking cleanup that already correctly captures meaningful interaction time.
- Update `backend/content/views.py`'s `mark_read` endpoint (or add a new one, e.g. `mark_in_progress`) accordingly — check current endpoint structure and adjust/add as needed to support both states.
- Update `CoursesScreen.js`'s status circle rendering (currently shows checkmark for read, empty circle for unread, ring for "current") to show a THIRD visual state for "in progress" (e.g., a half-filled circle or different color) — check current `CheckCircle` component and extend it.
- Update the admin's session-completion display (participant stats page, `EngagementLogInline`/`SessionCompletionInline` if still relevant, `ParticipantSession` admin display) to reflect the new in-progress state where shown.

## BUG 2 & 4: Inflated "Sessions Read" and "VJ Submitted" counts in admin

**Problem:** Participant list page (`/admin/participants/participant/`) shows wildly inflated counts (e.g., "25" sessions read for someone actually on session 2.2, "25/7" VJ submissions for someone with exactly 1 real submission). This strongly suggests a **query aggregation bug** — likely a `Count()` annotation across a JOIN that's fanning out (e.g., joining `ParticipantSession` and `VoiceJournalEntry` in the same queryset without `distinct=True` on the counts, causing each session-read row to multiply by each VJ entry row, or similar cross-join inflation).

**Fix:**
- Locate wherever these counts are computed for the participant list (`ParticipantAdmin.list_display`, likely custom methods like `sessions_read_count`/`vj_submitted_count` or similar, possibly using Django's `annotate(Count(...))` — check `backend/participants/admin.py`).
- If using `annotate` with multiple `Count()` calls on different related sets in the same queryset, add `distinct=True` to each `Count()` — this is the most common cause of exactly this symptom (multiplicative fan-out when annotating counts across more than one reverse-FK relationship simultaneously).
- Alternatively, if performance/complexity allows, compute each count as a separate method using `.count()` on the actual filtered queryset per participant (simpler, avoids the JOIN fan-out entirely, though slightly less performant at scale — acceptable given current participant volume).
- **Verify against ground truth:** for the specific participant mentioned (on session 2.2, should show "read: 1" — meaning only session 1.1's actually been marked read/completed if they're currently ON 2.2 mid-progress — or however many sessions truly precede their current position), confirm the corrected count matches manual inspection via `ParticipantSession.objects.filter(participant=p, is_read=True).count()` and `VoiceJournalEntry.objects.filter(participant=p).count()` run directly in shell.

## BUG 3: "Go to Home" button copy

**Fix:** In `SurveyScreen.js`, find the button text `"Go to Home"` (or wherever the post-VJ-submission thank-you screen's button label is defined) and change it to `"Go Home"`.

## UX 6: Surface enrollment/transfer code directly on the participant list

**Problem:** Generating a device transfer code currently requires: select participant → run action → then open into that specific participant's detail page → find the `enrollment_code` field to actually see the generated code. Too many clicks for a routine task.

**Fix:** Add the current `enrollment_code` value as a visible column in `ParticipantAdmin.list_display` on the main participant list page (`/admin/participants/participant/`) — likely near the existing "Is enrolled" column, per the stakeholder's suggestion. Show the code directly there (or "—" if none is currently set/pending). This means after running "Generate device transfer code" (or the other generate actions) via the bulk action on the list page, the admin can immediately see the resulting code right there in the same table, without navigating into each participant individually.

## BUG 7: Latest Emotion not showing on participant stats page

**Problem:** The participant stats page (`participant_stats.html`, built in an earlier task) has a "Latest Emotion" tile in the Tracking Summary bar, but it's showing "—" even when the participant has a real Voice Journal submission with an emotion recorded.

**Fix:** Check `backend/participants/admin.py`'s `stats_view` — it should already be computing something like `latest_emotion` from the most recent `VoiceJournalEntry` for that participant (this existed in an earlier task: `vj_entries.last().get_emotion_label_display() if vj_entries.exists() else '—'`). Debug why this isn't populating correctly now — possible causes: the `vj_entries` queryset ordering might not actually be returning the truly most recent entry (check `.order_by(...)` — `.last()` depends on correct ordering being applied first), or the `emotion_label` field might be empty/null on the actual VJ entry created via the real recording flow (as opposed to earlier manually-created test entries that had emotion values seeded directly). Investigate the actual current data first (check a real participant's most recent `VoiceJournalEntry.emotion_label` value directly in shell) before assuming which layer is broken.

## UX 8: Back button on key admin pages

**Requirement:** Add a "← Back" link/button at both the TOP and BOTTOM of the following admin pages, to avoid needing to scroll back up to use the default Django breadcrumb (which only exists at the top and isn't accessible after scrolling down a long form):
- Participant change form (`/admin/participants/participant/<id>/change/`)
- Cohort start date list (`/admin/participants/cohortstartdate/`)
- Session list (`/admin/content/session/`)
- Session change form (`/admin/content/session/<id>/change/`)
- Engagement log list (`/admin/content/engagementlog/`)
- Daily notification settings change form (`/admin/content/dailynotificationsettings/<id>/change/`)

**Approach:** Since several of these already have custom `change_form.html`/`change_list.html` template overrides (participant, daily notification settings, session — check which ones already have overrides from earlier tasks vs. which use Django's default templates), the cleanest approach is a small, reusable back-button template snippet/include (e.g., `templates/admin/_back_button.html`) that takes the target URL as a parameter, included at both the top and bottom of each relevant template. For pages that don't yet have a custom template override, create a minimal one (extending the appropriate Django admin base template) whose only job is adding this button in both positions, to avoid needing to rebuild the whole page from scratch. The back button's target: use browser history (`javascript:history.back()`) OR a specific "back to list" URL for change-form pages, and "back to admin home" for list pages — use your judgment on whichever makes the most intuitive sense per page type, but keep it consistent across all the listed pages.

---

## What NOT to change
- Do NOT change any content-scheduling logic (waitlist, cohort start dates, day/week unlocking, session overrides) — unrelated to this batch.
- Do NOT change the notification system (daily/scheduled triggers, sending logic) — unrelated, already working and tested tonight.
- Do NOT change VJ recording storage (still local `MEDIA_ROOT`, not S3 — that's a separate, larger task noted elsewhere, not part of this batch).

## Testing expectations
- Open a session, immediately navigate away without interacting — confirm it shows "in progress," NOT "read/completed."
- Open a session, spend meaningful time (matching the existing engagement threshold), leave — confirm it now shows "completed"/"read."
- Check the participant list's "Sessions Read" and "VJ Submitted" columns against real ground-truth counts (verified via direct shell queries) for at least 2-3 different participants with varying amounts of real activity — confirm counts now match exactly, no more inflation.
- Confirm "Go Home" button text is corrected on the VJ thank-you screen.
- Confirm `enrollment_code` is visible directly on the participant list page, updates correctly after generating a new code via any of the existing generate actions.
- Confirm "Latest Emotion" on the stats page correctly shows a real participant's most recent VJ emotion, not "—", for a participant with at least one real submission.
- Confirm back buttons appear at top AND bottom of all six listed admin pages, and correctly navigate as expected.
- Run `python manage.py check` and confirm any new migrations (if `ParticipantSession` gets a new status field) apply cleanly.
