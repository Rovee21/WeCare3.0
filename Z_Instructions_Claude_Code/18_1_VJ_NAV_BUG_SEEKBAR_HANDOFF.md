# WECARE 3.0 — VJ Navigation Bug Fix + Playback Seek Bar

## Context
Building on the just-completed VJ History + Playback feature. Two issues surfaced during live on-device testing.

## Bug: Journal tab stuck on History screen after visiting it

**Reproduction steps:**
1. From Home screen, tap "View History" → navigates into the Journal stack's History screen.
2. Navigate back to Home (via back button or Home tab).
3. Tap the Voice Journal tab/card again (intending to make a NEW recording).
4. **Bug:** instead of landing on the recording screen (mic circle), it goes back to the History screen again. Only a full app reload fixes it — after reload, tapping Voice Journal correctly goes to the recording screen.

**Root cause (likely):** `JournalNavigator` (the stack inside `RootNavigator.js` handling `VoiceJournalScreen` → `SurveyScreen` → the new `VoiceJournalHistoryScreen`) is probably retaining its last-visited screen as the "current" position in the stack, since React Navigation stacks by default preserve navigation state across tab switches unless explicitly reset. Tapping into the Journal tab again re-enters the stack wherever it was last left (on `VoiceJournalHistoryScreen`), rather than resetting to the stack's initial route (`VoiceJournalScreen`, the recording landing screen).

**Fix:** Ensure that navigating to the Journal tab/stack from OUTSIDE it (i.e., from the Home screen's "tap to record" action specifically, and ideally the tab bar's Journal icon too) always resets the Journal stack back to its initial screen (`VoiceJournalScreen`), rather than resuming wherever it was left. Two common approaches, pick whichever fits the existing navigation setup best:
- Use `navigation.navigate('Journal', { screen: 'VoiceJournalScreen' })` with an explicit target screen when navigating INTO the Journal tab from Home, rather than a bare `navigation.navigate('Journal')`.
- OR configure the tab navigator/stack with a listener that resets the Journal stack to its initial route whenever the tab is pressed while already focused, or whenever entered via the Home screen's recording action specifically (check React Navigation's `tabPress` listener pattern, or `unmountOnBlur`/`resetOnBlur`-style options if using a version of React Navigation that supports them for nested stacks — check what's actually installed/available given the project's current React Navigation version before assuming a specific API).

**Important distinction:** the History screen itself, when reached via its own "View History" button (either from Home or from the VJ landing screen), should still work exactly as it does now — this fix is specifically about ensuring that INTENTIONALLY navigating to make a new recording (tapping the main Home Voice Journal card action, not the History button) always lands on the recording screen, regardless of what the Journal stack's last state was.

## Enhancement: Seek bar / progress bar on playback (pre-submission confirmation screen)

**Current state:** the confirmation screen (added in the previous task) has a simple Play/Pause button using `useAudioPlayer`/`useAudioPlayerStatus`, but no visual progress indicator or ability to scrub/seek to a specific point in the recording.

**Add:**
- A progress bar showing current playback position relative to total duration (e.g., using React Native's `Slider` component — check if `@react-native-community/slider` is already a dependency; if not, it's a well-established, standard library worth adding, OR use a simpler custom `View`-based progress bar if avoiding a new dependency is preferred — your call on which is more idiomatic given what's already used elsewhere in the app, but a real draggable slider is specifically requested, not just a static progress indicator).
- The slider should be **draggable** — allow the participant to grab and drag to any point in the recording, and on release, seek the player to that position (`expo-audio`'s player should support a `seekTo`-style method or setting `currentTime` directly — check its current API).
- Show elapsed time / total duration as text near the slider (e.g., "0:12 / 0:47"), using the player status's current position and duration values (already available via `useAudioPlayerStatus`, given it's already being used for the Play/Pause button).
- Update the slider's position in real-time as playback progresses (this should come naturally from `useAudioPlayerStatus` re-rendering as position updates, same pattern already in use).

**Scope check — is this ALSO wanted on the History screen's per-entry playback**, or just the pre-submission confirmation screen? Default to adding it to BOTH (the confirmation screen AND the History screen's playback, since they're both "listen to my own recording" contexts and a consistent experience between them seems reasonable) — but if the History screen's simpler play/pause-only UI turns out to be significantly more complex to extend with a full seek bar per list-row (given it's a `FlatList` with potentially many rows, a full slider per row could be visually busy), a reasonable simplification for the History screen specifically is: keep History as simple play/pause only (no seek bar), and add the full seek bar UI ONLY to the pre-submission confirmation screen (where there's only ever one recording being reviewed at a time, so extra UI real estate for a slider is less visually crowded). Use judgment here and clearly state which approach was taken in the summary.

## What NOT to change
- Do NOT change the underlying recording logic, upload logic, or the History endpoint itself — this task is scoped to navigation-stack behavior and the playback UI enhancement only.
- Do NOT change the SurveyScreen.js emotion/stress picker or submission flow — unrelated.
- Do NOT remove or alter the existing Play/Pause button — the seek bar is an ADDITION alongside it (or the Play/Pause button can be visually integrated with/near the slider, your call on the cleanest layout, but the ability to simply play/pause should remain).

## Testing expectations
- Reproduce the exact bug sequence described above (Home → View History → back to Home → tap Voice Journal to record) — confirm it now correctly lands on the recording screen (mic circle), not the History screen.
- Confirm visiting History via either entry point still works correctly afterward, and that the fix doesn't break the ability to reach History at all — only fixes the "stuck there when trying to record" issue.
- Confirm the seek bar shows accurate elapsed/total time, updates smoothly during playback, and correctly seeks to a new position when dragged and released, resuming playback from that point (or pausing at that point if not currently playing — either behavior is acceptable, use whichever expo-audio makes simpler).
- If seek bar was added to History screen playback too, confirm it works correctly per-row without interference between rows (only one row's audio should ever play at a time — confirm switching rows correctly stops/replaces the previous row's playback, consistent with the previous task's single-player-instance approach).
