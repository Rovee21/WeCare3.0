# WECARE 3.0 — Full-Screen Waitlist Lockout (Replace Per-Tab Messages)

## Context
Just implemented and confirmed working: cohort-based `program_start_date` + `is_waitlisted` on the participant profile, with Home and Courses screens each independently showing a waitlist message when `is_waitlisted` is true. This works correctly on those two screens, but the Voice Journal tab was NOT updated — a waitlisted participant can still open it, see the microphone permission prompt, and reach the recording UI, even though any submission wouldn't really be meaningful yet. Rather than patching every individual screen one at a time, stakeholder wants a much simpler, more robust approach: **replace the entire tab-based app shell with a single, simple waitlist screen (plus a contact option) for any waitlisted participant** — no bottom tab bar, no way to reach Courses/Journal/Settings/Contact tabs at all while waitlisted.

## Requirement

### Replace the whole `MainTabs` navigator with a dedicated waitlist flow when waitlisted
In `mobile/src/navigation/RootNavigator.js`, after fetching the participant's profile (check current pattern — the app already fetches `GET /api/profile/` on Home/Courses focus per the previous task; for this task, the check likely needs to happen earlier, at the root-navigation level, right after determining the participant has a valid token) — if `is_waitlisted` is true, route to a NEW, separate simple screen/flow instead of `MainTabs` entirely. This means the bottom tab bar (Home/Courses/Journal/Contact/Settings icons) should not render at all for a waitlisted participant — not just individual tab content being empty/blocked, the tab bar itself should be absent.

**Concretely:**
- Add a new screen, e.g. `WaitlistScreen.js`, that shows:
  - A clear message: "Thank you for enrolling! You're on the waitlist. Your program starts on [formatted program_start_date]" (or the existing "coming soon" fallback text if `program_start_date` is null — reuse the exact wording/formatting already built for the Home/Courses waitlist messages in the previous task, don't invent new copy).
  - A way to reach contact info — either a simple "Contact Us" button/link on the same screen that navigates to the existing `ContactUsScreen.js` (reuse that existing screen, don't rebuild it), or, if simpler, just inline the coordinator phone/email directly on the waitlist screen itself (check what `ContactUsScreen.js` currently shows and reuse that content/that screen via navigation — whichever is less code duplication).
  - Nothing else — no buttons to Courses, Journal, Settings, or Home. This is the ENTIRE app experience for a waitlisted participant.
- Wire this into `RootNavigator.js`'s stack: when the app determines a logged-in participant `is_waitlisted`, navigate to this waitlist flow instead of `MainTabs`. Structure it as its own small stack (waitlist message screen → optional contact screen) OR a single screen with an embedded contact section — your call on which is cleaner given the existing navigation setup, but the key requirement is: no bottom tab bar, no access to Courses/Journal/Home/Settings screens while waitlisted.

### Revert/simplify the per-screen waitlist messages added in the previous task
Since Home and Courses will no longer be reachable at all by a waitlisted participant (they never enter `MainTabs` in the first place), the waitlist-specific conditional rendering added to `HomeScreen.js` and `CoursesScreen.js` in the previous task becomes dead code — a waitlisted participant will never see those screens now. Remove that conditional logic from `HomeScreen.js` and `CoursesScreen.js`, reverting them to simply always show their normal (non-waitlisted) content, since by the time a participant reaches those screens at all, they're guaranteed not to be waitlisted (the routing decision now happens earlier, at the root level). This simplifies those two files back down and avoids maintaining the same waitlist-check logic in three+ places.

### What happens when a waitlisted participant's cohort start date arrives
This should already work naturally with no extra code: next time the app checks the profile (app reopen, or whatever triggers a re-check — check how `RootNavigator.js` currently determines initial route, likely on app launch/focus) and `is_waitlisted` is now false, they should route into the normal `MainTabs` experience instead. Don't build any special "transition" animation or in-app polling for this — a simple re-check on next app open/focus is sufficient.

## What NOT to change
- Do NOT change the backend `is_waitlisted` / `program_start_date` logic — already correct and verified from the previous two tasks.
- Do NOT change `ContactUsScreen.js`'s actual content — just reuse/navigate to it (or copy its content inline) as needed for the waitlist flow's contact option.
- Do NOT change the Voice Journal screens themselves (`VoiceJournalScreen.js`, `SurveyScreen.js`) — they're simply now unreachable for waitlisted participants via the tab bar removal, no internal changes needed to those files.
- Do NOT add any push notification or polling mechanism to auto-detect when the waitlist period ends — a normal app-open re-check is sufficient, per the previous section.

## Testing expectations
- A waitlisted participant (per the existing test setup: cohort start date in the future) opens the app → lands on the single waitlist screen, with NO bottom tab bar visible at all, and no way to navigate to Courses/Journal/Home/Settings.
- The waitlist screen shows the correct "Your program starts on [date]" message (or the "coming soon" fallback if unset), matching the same text/formatting as before.
- The contact option on the waitlist screen works — either navigates to `ContactUsScreen.js` successfully, or shows the correct contact info inline, whichever approach was chosen.
- Update the cohort's `program_start_date` to the past (simulating the wait period ending) — reopen/reload the app, confirm the SAME participant now correctly lands in the normal `MainTabs` experience (bottom tab bar visible, Home shows real "Today's Session" content, Courses shows the real session list) — proving the transition out of waitlist mode works correctly.
- Confirm a NON-waitlisted participant's experience is completely unaffected — normal tab bar, normal Home/Courses/Journal/Settings/Contact all working exactly as before, with the now-simplified (reverted) `HomeScreen.js`/`CoursesScreen.js` no longer containing waitlist-conditional logic.
