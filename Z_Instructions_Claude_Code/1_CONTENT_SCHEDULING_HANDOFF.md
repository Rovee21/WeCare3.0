# WECARE 3.0 — Content Scheduling Feature: Handoff Brief

## Context
This is a Django + React Native (Expo) monorepo at `WeCare3.0/` with `backend/` (Django REST Framework) and `mobile/` (Expo/React Native, mixed JS/TS after a recent codegen migration). Docker Compose runs the backend locally (`docker-compose up` in `backend/`). Mobile runs via `npx expo start --clear` from `mobile/`, using `.env` for `EXPO_PUBLIC_API_URL`.

The task below is a new feature: **date-based content scheduling / drip delivery**. Implement it end to end — backend logic, serializer changes, and mobile UI for locked/grayed sessions.

---

## Current State (relevant facts)

- `Participant` model (`backend/participants/models.py`) has `enrolled_at` (DateTimeField) and `enrollment_week` (PositiveSmallIntegerField, currently just a plain field, not actively used for gating).
- `Participant.current_week_number` property already exists: calculates week based on `(now - enrolled_at).days // 7 + 1`, capped at 7.
- `Session` model (`backend/content/models.py`) has `week_number` and `day_number` (both PositiveSmallIntegerField), plus `target_group1/2/3` for cohort targeting (already works, tested, don't break it).
- `content/views.py` has `_filter_sessions_for_participant(participant)` which currently only filters by cohort (group1/2/3 matching) — returns ALL sessions matching cohort regardless of date. This is the function that needs the new gating logic added.
- `session_list` and `session_today` views both call `_filter_sessions_for_participant`.
- `SessionSerializer` (`backend/content/serializers.py`) returns fields including `id, title, title_zh, week_number, day_number, week_label, media_types, video_url, audio_url, text_content, text_content_zh, resources, is_read`. Need to add a `locked` boolean field.
- `ParticipantSession` model tracks read/unread state per participant per session (`is_read`, `read_at`).
- Mobile `CoursesScreen.js` renders sessions grouped by week via `groupByWeek()`, using a `CheckCircle` component that shows read/unread/current state. Needs a locked state added.
- Each week is designed to have **exactly 6 sessions** (day_number 1-6). Day 7 is an intentional rest day — no session scheduled.

---

## Feature Requirements (confirmed with stakeholder)

### 1. Day-based unlocking within a week
- Day 1 of a week unlocks immediately when that week starts.
- Day 2 unlocks 1 calendar day later, Day 3 two days later, etc. (`unlocked_day_number = days_since_week_start + 1`, capped at 6).
- No weekend pausing — strictly calendar days, 7 days a week.

### 2. Week-to-week gating (BOTH conditions must be true to unlock next week)
- At least 7 days have passed since the current week started, AND
- All 6 sessions in the current week are marked as read (`ParticipantSession.is_read = True` for all 6).
- If either condition fails, the next week stays locked entirely (not even shown).

### 3. Manual override
- Admins can manually bump a participant to a specific week via the **existing** `enrollment_week` field in Django Admin, bypassing the automatic 7-day/completion gate.
- Need a helper method on `Participant`, e.g. `effective_current_week()`, that returns `max(automatic_week_calculation, enrollment_week_override)` — i.e., admin override can only push forward, never lock someone out of where they've already progressed. Clarify/decide the exact precedence logic as you implement (reasonable default: if `enrollment_week > automatic_week`, use `enrollment_week`; otherwise use the automatic calculation).
- Update the Django Admin field description for `enrollment_week` to clarify it's a manual override for this purpose (currently the field exists but its exact purpose in the app isn't documented).

### 4. Visibility rules — "visible but locked", not fully hidden (for current week only)
- For sessions in the participant's **current effective week**: show ALL 6 sessions, but any session whose `day_number` hasn't unlocked yet (per rule #1) should be marked `locked: true` in the API response.
- For **future weeks** (beyond current effective week): return NO sessions at all — not even locked placeholders. Fully absent from the API response.
- For **past/completed weeks**: fully visible and accessible as before (read or unread), no locking applied — participants can always revisit completed weeks.

### 5. Mobile UI changes
- In `CoursesScreen.js`, sessions with `locked: true` from the API should render with a lock icon (🔒) instead of the current checkmark/circle/dot states, and tapping them should not navigate to `DailySessionScreen` (make the `TouchableOpacity` a no-op or disabled for locked items).
- Preserve all existing behavior for unlocked/read/unread sessions.

---

## What NOT to change
- Do not touch cohort targeting logic (`target_group1/2/3` matching) — it's already implemented and tested, just add date-gating on top of it in the same filter function.
- Do not change the `Session` or `ParticipantSession` model schemas beyond what's needed (no new fields should be required for this — the logic can be computed from existing `enrolled_at`, `week_number`, `day_number`, and `is_read` data).
- Do not break the existing engagement tracking (`EngagementLog`), Voice Journal integration, or Voice Journal screens — unrelated to this feature.

## Testing expectations
- After implementing, test manually via Django shell or the admin: create a test participant with `enrolled_at` set to various points in the past (e.g., today, 3 days ago, 8 days ago, 10 days ago with all week 1 sessions marked read) and confirm `_filter_sessions_for_participant` returns the expected locked/unlocked/hidden sessions for each scenario.
- Confirm the mobile Courses screen correctly shows lock icons and prevents navigation on locked sessions.
- Confirm cohort targeting still works correctly alongside the new date gating (run existing manual cohort test if one exists, or recreate: a fake "control" vs "intervention" participant should still only see their targeted sessions, now also respecting date locks).

## Migration note
`makemigrations` / `migrate` should NOT be needed for this feature since no new model fields are required — this is pure business logic in the view layer plus a serializer field and a model helper method. If you find you do need a new field, flag it clearly before adding it, since the stakeholder wants to confirm any schema changes.
