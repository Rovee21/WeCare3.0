# WECARE 3.0 — Content Scheduling: Sequential Unlock Addendum

## Context
This is a follow-up refinement to the content-scheduling feature just implemented (date-based day/week unlocking in `_filter_sessions_for_participant`, `Participant.automatic_gated_week()`, `unlocked_day_number()`, etc. in `backend/participants/models.py` and `backend/content/views.py`). That feature is done and verified. This addendum adds ONE more rule on top of it.

## New Requirement: Sequential completion within a week

**Problem confirmed via manual testing:** Currently, if enough calendar days have passed, a participant can jump directly to e.g. Day 4 of a week even if they haven't read Day 1, 2, or 3 yet. This should not be allowed.

**New rule:** A session within the participant's current week is only unlocked (tappable, not `locked: true`) if BOTH:
1. It passes the existing calendar-day gate (`unlocked_day_number` logic — unchanged), AND
2. **NEW:** All sessions in that same week with a lower `day_number` are already marked read (`ParticipantSession.is_read = True`) for this participant.

If condition 2 fails (an earlier day in the same week isn't read yet), the session should be `locked: true` even if condition 1 (the calendar date) would otherwise allow it.

**Example confirmed by stakeholder testing:**
- Participant enrolled 11 days ago, has NOT read Day 1, 2, or 3 yet.
- Even though 11 days have passed (way more than enough to calendar-unlock all 6 days of the week), Day 4, 5, 6 must show as `locked: true` until Day 1, 2, 3 are read in order.
- Once Day 1 is read, Day 2 becomes unlockable (assuming its calendar gate also passes — which it will, since day 2's gate is looser than day 1's gate in this scenario). Day 3 remains locked until Day 2 is read. And so on.
- This composes with the existing week-to-week gate: Week 2 should NOT unlock until all 6 sessions in Week 1 are read AND 7 days have passed — this part already works correctly and should not change.

## Where to implement
Most likely in `_filter_sessions_for_participant` in `backend/content/views.py`, right where `session.locked` is currently being set based on `unlocked_day_number()`. Add the additional check: for each session in the current week, also verify all sessions with lower `day_number` in that same week have a corresponding `ParticipantSession` with `is_read=True` for this participant. If not, force `locked = True` regardless of what the calendar-day check said.

Be efficient about this — don't do it with N+1 queries per session; consider fetching the participant's read session IDs for the current week once, then checking membership in a set/list as you iterate through the week's sessions in `day_number` order.

## What NOT to change
- Do not change the week-to-week gating logic (`automatic_gated_week`, 7-day + full-week-read requirement) — already correct.
- Do not change the calendar day-unlock calculation (`unlocked_day_number`) — still needed as one of the two conditions.
- Do not change cohort targeting.
- No new model fields / migrations should be needed — this can be computed from existing `ParticipantSession.is_read` data, same as the rest of the feature.

## Testing
Re-verify the scenario the stakeholder just manually tested:
- Enroll a test participant 11 days ago, don't mark anything read.
- Confirm Day 1 shows unlocked, Days 2-6 show `locked: true` (since Day 1 isn't read, even though calendar allows Day 2+).
- Mark Day 1 as read (via `POST /sessions/<id>/read/` or the app). Confirm Day 2 becomes unlockable, Day 3-6 still locked.
- Continue through Day 6. Once all 6 are read (and since 11 days already passed, satisfying the 7-day gate), confirm Week 2 sessions appear.
- Also re-run the earlier scenario (partial completion, e.g. only Day 4 read while 1-3 unread) and confirm Week 2 correctly stays hidden — this should already work from the previous implementation, just confirm it still holds with the new sequential rule layered in.
