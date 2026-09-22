# WECARE 3.0 — Voice Journal History + Playback

## Context
Current VJ flow: `VoiceJournalScreen.js` (recording landing screen, mic circle, prompt) → record → confirmation screen ("Recording Complete! Are you sure you want to submit?" with Submit/Re-record options) → `SurveyScreen.js` (emotion + stress picker → submit → thank-you screen with "Go Home" button, just renamed from "Go to Home" in a parallel bug-fix task, check current text before assuming).

Backend: `VoiceJournalEntry` model (`backend/journal/models.py`) stores `participant`, `week_number`, `audio_s3_key` (empty currently — see storage note below), `audio_file` (local FileField, actual current storage location), `recording_seconds`, `transcript`, `vj_stress_level`, `emotion_label`, `transcription_status`, `submitted_at`. Currently NO endpoint exists for a participant to fetch their own VJ history — this task needs to build one.

**Storage note (do not act on this in this task):** VJ audio currently saves to local `MEDIA_ROOT` on the server (not S3) — this is intentional for now; a separate future task will migrate to S3. Playback should work against whatever URL the file currently has (local `audio_file.url`), and will continue working after a future S3 migration without changes to the playback code itself, since it just needs a working URL either way.

## Requirement

### 1. Backend: VJ history endpoint
Add `GET /api/journal/history/` (or similar, matching existing URL conventions in `backend/journal/urls.py`) — authenticated, returns the requesting participant's OWN past `VoiceJournalEntry` records only (never another participant's), ordered most-recent-first. Response per entry should include: `id`, `week_number`, `submitted_at`, `emotion_label` (human-readable display value, not just the raw choice key), `vj_stress_level`, `recording_seconds`, and an `audio_url` (the playable URL — `request.build_absolute_uri(entry.audio_file.url)` or similar, so the mobile app gets a fully-qualified URL it can hand directly to an audio player, not a relative path).

### 2. Mobile: Add playback to the post-recording confirmation screen
On the existing confirmation screen (in `VoiceJournalScreen.js`, the "Recording Complete!" step, before final submission) — add a play/pause control so the participant can listen to their own recording before deciding to submit or re-record. Use `expo-audio`'s playback capabilities (already a dependency, used for recording — check its player/playback API, likely a similar `useAudioPlayer`-style hook or `createAudioPlayer`, consistent with how `expo-video`'s `useVideoPlayer` pattern was used elsewhere in this codebase for a similar play/pause UI). The recorded file's local URI (already available immediately after stopping recording, before upload) is what gets played here — no network/backend involved at this stage, purely local file playback.

### 3. Mobile: "View History" button on Home screen
On `HomeScreen.js`'s existing Voice Journal card (currently shows "Your Last Entry: ..." or similar, check current copy) — make the card slightly larger and add a "View History" button/link within it, navigating to the new History screen (see #5). Keep the existing "tap to record this week's entry" affordance working as it currently does (tapping the main card area still goes to the recording flow) — the History button is an additional, distinct tap target within the same card, not a replacement.

### 4. Mobile: "View History" button + recording animation on the VJ landing screen
On `VoiceJournalScreen.js`'s initial landing state (prompt + mic circle, before recording starts):
- Add a "View History" button below the mic circle, navigating to the new History screen (see #5).
- When the participant taps the mic circle to START recording: animate the "View History" button to fade out (e.g., `Animated.timing` opacity to 0, or React Native's `LayoutAnimation`/`Animated` API — whichever is more idiomatic given what's already imported in this file) so it's not tappable while recording is in progress. Simultaneously, animate the mic circle to grow larger (e.g., scale transform via `Animated.timing`), giving clear visual feedback that recording is active. Reverse both animations if recording is stopped/cancelled and the participant returns to the landing state (e.g., via "re-record" from the confirmation screen).

### 5. Mobile: New History screen
Add `VoiceJournalHistoryScreen.js` — on mount, calls the new `GET /api/journal/history/` endpoint, displays a scrollable list of past entries. Each entry shows: date (formatted from `submitted_at`), week number, emotion (display label), stress level, and a play/pause button to play back that specific recording using its `audio_url` from the API response. Handle empty state gracefully (no past entries yet — show a friendly message, not a blank/broken screen). Wire this screen into whatever navigator currently handles the Journal tab's stack (check `RootNavigator.js`'s `JournalNavigator` — add this as a new screen in that stack, reachable via navigation from both entry points in #3 and #4).

## What NOT to change
- Do NOT touch VJ audio storage/upload logic (`direct_upload` view, local `MEDIA_ROOT` storage) — unrelated, a separate future S3-migration task will handle storage changes. This task only ADDS playback/history capability on top of however storage currently works.
- Do NOT change the actual recording/submission flow's core logic (permission requests, `expo-audio` recording setup, the emotion/stress survey, the final `directUpload` call) — only add the NEW playback control to the confirmation screen and the new History screen/navigation; don't restructure what's already working.
- Do NOT build any admin-side changes — this task is entirely participant-facing (mobile app + one new read-only backend endpoint scoped to the requesting participant's own data).
- Do NOT implement any editing/deleting of past VJ entries from the History screen — view + playback only, per stakeholder's stated scope.

## Testing expectations
- Record a VJ entry, on the confirmation screen tap play — confirm the just-recorded audio plays back correctly before submission.
- From the Home screen, tap "View History" — confirm it navigates to the History screen.
- From the VJ landing screen, tap "View History" (before starting a recording) — confirm same navigation works from this second entry point too.
- Tap the mic circle to start recording — confirm the "View History" button visibly fades out and becomes untappable, and the mic circle visibly grows, with a smooth (not jarring/instant) animation.
- Stop recording, tap "re-record" from the confirmation screen — confirm the landing screen's "View History" button and mic circle sizing correctly reset back to their normal state, ready for a fresh recording attempt.
- On the History screen, confirm past entries show correct date, week, emotion, and stress level, matching what's actually in the database for that participant (cross-check via Django shell/admin).
- Confirm the History endpoint only ever returns the authenticated participant's OWN entries — test with two different participants' tokens, confirm no cross-participant data leakage.
- Tap playback on a history entry — confirm that specific past recording plays correctly.
- Confirm an empty-history state (a participant with zero past VJ submissions) shows a reasonable message, not a crash or blank screen.
- Run `python manage.py check` for the backend endpoint addition.
