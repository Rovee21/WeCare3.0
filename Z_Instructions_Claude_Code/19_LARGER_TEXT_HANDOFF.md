# WECARE 3.0 — Larger Text Sizes App-Wide (Accessibility)

## Context
WECARE's participant base skews older (caregivers of individuals with ADRD, often themselves older adults). Current text sizing across the app uses typical mobile app defaults, which may be too small for comfortable reading by this population. Stakeholder wants text sizes increased across the app for better accessibility/readability.

## Requirement

### Increase base font sizes across all participant-facing screens
Go through every screen's `StyleSheet.create(...)` block in `mobile/src/screens/` and increase `fontSize` values across the board. General guidance:
- Body text / paragraph content: increase by roughly 15-20% from current values (e.g., 14→16-17, 15→17-18)
- Headings/titles: increase proportionally as well, maintaining the existing visual hierarchy (headings should still look clearly larger than body text after the change, not collapse toward the same size)
- Button labels: increase slightly, but ensure buttons don't visually break/overflow at the new size — check button padding/sizing still accommodates larger text comfortably
- Small/secondary text (timestamps, captions, helper text): increase modestly, but these can stay proportionally smaller than body text — don't force everything to be identically large, just shift the whole scale up

**Screens to cover** (check `mobile/src/screens/` for the full current list, but at minimum): `HomeScreen.js`, `CoursesScreen.js`, `DailySessionScreen.js`, `VoiceJournalScreen.js`, `SurveyScreen.js`, `VoiceJournalHistoryScreen.js` (if already built by a parallel task — check if it exists yet), `SettingsScreen.js`, `ContactUsScreen.js`, `EnrollmentScreen.js`, `WaitlistScreen.js`.

**Approach — prefer a centralized scale if reasonably easy:** rather than manually adjusting dozens of individual `fontSize` values scattered across files (error-prone, hard to keep consistent), check if there's already a shared constants/theme file (e.g., `mobile/src/constants/colors.js` exists per earlier work — check if a sibling `typography.js`/`fontSizes.js` exists, or if font sizes are just hardcoded per-screen currently). If font sizes are currently ad-hoc/hardcoded per screen with no shared scale, consider introducing a simple shared scale (e.g., a `Typography` or `FontSizes` constant object with named sizes like `small`, `body`, `heading`, `title`) and migrating screens to use it — this makes future adjustments (if the team wants to tune further) much easier than another full find-and-replace pass. Use your judgment on whether this refactor is worth doing now vs. just directly bumping the hardcoded values in place — given this is likely to be iterated on again based on team feedback, a shared scale is probably worth the modest extra effort, but don't let this turn into an overly large refactor either; keep it pragmatic.

### Do NOT touch the Django Admin console's styling
This task is scoped to the PARTICIPANT-FACING MOBILE APP ONLY. Do not change any admin console CSS/templates — text sizing there is a separate, unrelated concern (admin users are the research team, not the older-adult participant population this task is addressing).

## What NOT to change
- Do NOT change any layout structure, navigation, or functionality — this is purely a text-sizing/styling pass.
- Do NOT change colors, spacing, or other non-font styling unless a font size increase mechanically requires a small adjacent adjustment (e.g., a button needs slightly more padding to comfortably fit larger text without visually cramming) — keep such adjustments minimal and only where genuinely necessary to accommodate the larger text.
- Do NOT touch the Django Admin console.
- Do NOT change font sizes used in the Voice Journal recording screen's countdown timer or other precise numeric displays if increasing them would cause layout issues — use judgment, but flag any screen where you chose NOT to increase text size and explain why in your summary.

## Testing expectations
- Visually confirm text is noticeably larger and more readable across all listed screens, without any text overflow, truncation, or broken layouts (buttons, cards, list items all still render cleanly).
- Confirm existing visual hierarchy is preserved — headings still clearly read as more prominent than body text, body text still clearly more prominent than captions/secondary text.
- If a shared typography scale was introduced, confirm it's actually being used consistently across the touched screens (not just introduced but left partially unused).
- Spot-check on both a smaller and larger device screen size if possible (or at minimum confirm nothing looks broken in the standard simulator/emulator size used for other testing) to catch any overflow issues introduced by the larger text.
