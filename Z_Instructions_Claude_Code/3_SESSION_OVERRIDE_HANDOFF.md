# WECARE 3.0 — Session-Level Admin Override

## Context
This is a follow-up feature building directly on the content-scheduling work already implemented and verified (date-based day/week unlocking with sequential-read requirement, in `backend/content/views.py`'s `_filter_sessions_for_participant`, plus `Participant.automatic_gated_week()`, `effective_current_week()`, `unlocked_day_number()` in `backend/participants/models.py`). There's also an existing week-level manual override via the `enrollment_week` field on `Participant` (admin can bump someone's effective week forward).

This feature adds a finer-grained override: **per-participant, per-session** manual unlock/lock, independent of the automatic day/week/sequential logic.

## Requirement

Add the ability for an admin to force a specific session to be unlocked or locked for a specific participant, overriding whatever the automatic scheduling logic would otherwise compute.

### New model: `SessionOverride`
Add to `backend/content/models.py`:
- `participant` — FK to `participants.Participant`
- `session` — FK to `Session`
- `override_type` — CharField with choices: `"force_unlock"` / `"force_lock"`
- `set_by` — FK to Django's `User` model (nullable, so we know which admin made the change — for audit trail purposes, this is a research study and traceability matters)
- `created_at` — auto_now_add DateTimeField
- Add `unique_together = ["participant", "session"]` — only one override per participant/session pair at a time. If an admin sets a new override for a pair that already has one, it should replace/update it (not create a duplicate row) — use `update_or_create` semantics wherever this is created/edited, whether via Django Admin inline or any future API.

### Integration into unlock logic
In `_filter_sessions_for_participant` (`backend/content/views.py`), the override check should take priority over BOTH the day-based calendar gate AND the sequential-read gate — but should NOT bypass cohort targeting (`target_group1/2/3` matching) or the week-level gate (i.e., an override can't unlock a session in a week that hasn't started at all per `effective_current_week()` — overrides operate within the current visible week's session set, not to reach into completely future weeks that aren't shown at all). Clarify/decide precise interaction as you implement, but the intent is: overrides fine-tune locking within what's already surfaced by the week-level system, not bypass cohort/week visibility entirely.

Logic order should be something like: for each session already in scope (cohort-matched, within current effective week):
1. Check if a `SessionOverride` exists for this participant+session.
2. If `force_unlock` → `locked = False`, skip the day/sequential checks entirely for this session.
3. If `force_lock` → `locked = True`, skip the day/sequential checks entirely for this session.
4. If no override exists → fall back to existing day-based + sequential-read logic exactly as before.

### Django Admin UI
Add a `TabularInline` for `SessionOverride` on the `ParticipantAdmin` page (in `backend/participants/admin.py`), similar in style to how other inlines were set up before (though note: `EngagementLogInline`, `SessionCompletionInline`, `VoiceJournalInline` were later REMOVED from the participant edit page per a prior task — check current state of `inlines = []` before adding this one; this new inline SHOULD be added back, it's a deliberate exception since it's an actionable admin control, not a read-only stats display like the ones removed).

The inline should let the admin:
- Pick a `Session` from a dropdown (consider filtering/scoping to sessions relevant to that participant's cohort if reasonably easy, but not a hard requirement — a plain FK dropdown is acceptable if filtering is complex)
- Pick `override_type` (force_unlock / force_lock) from a dropdown
- Auto-set `set_by` to the currently logged-in admin user on save (override `save_model` or the inline's save behavior — don't make the admin manually pick themselves)
- Display `created_at` as read-only

## What NOT to change
- Do not modify the week-level gating (`automatic_gated_week`, `effective_current_week`) — unchanged.
- Do not modify cohort targeting matching logic — unchanged.
- Do not modify the day-based calendar gate or sequential-read gate logic itself — this feature only adds a bypass check before those run, doesn't alter how they compute when no override exists.
- Do not re-add the previously-removed `EngagementLogInline`, `SessionCompletionInline`, or `VoiceJournalInline` to the participant page — those were intentionally removed and should stay removed. Only add the new `SessionOverride` inline.

## Migration
This DOES require a new model and migration — that's expected and fine for this task (unlike the previous two scheduling tasks which were pure logic with no schema change). Run `makemigrations` and `migrate` as normal.

## Testing expectations
- Create a `SessionOverride` with `force_unlock` for a session that would otherwise be locked (e.g., Day 4 while Day 1-3 unread) — confirm the API now returns `locked: false` for that specific session, while other still-locked sessions remain locked.
- Create a `SessionOverride` with `force_lock` for a session that would otherwise be unlocked (e.g., Day 1) — confirm the API now returns `locked: true` for that session.
- Confirm removing/deleting an override reverts the session to normal automatic-logic behavior.
- Confirm cohort targeting still composes correctly — an override on a session that doesn't match the participant's cohort in the first place shouldn't cause it to appear (it should already be filtered out before the override check even applies — reconfirm this boundary explicitly).
- Confirm the `set_by` field populates correctly with the admin user who created the override via the Django Admin UI.
- Run `python manage.py check` and confirm migrations apply cleanly.
