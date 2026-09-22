# WECARE 3.0 — Track Actual Video Watch Time (After Pressing Play)

## Context
`DailySessionScreen.js` currently tracks `video_time_seconds` as "time spent with the Video tab active" (via `videoTimeRef`, accumulated in `handleTabChange` and the cleanup `useEffect`) — this measures tab dwell time, NOT whether the participant actually pressed play or how much of the video they watched. This was a deliberate simplification made earlier, with a stakeholder note that "time after pressing play" would be more meaningful for research purposes and could be added later. That later point is now.

The video player uses `expo-video`'s `useVideoPlayer` hook:
```javascript
const player = useVideoPlayer(course?.video_url || '', p => { p.loop = false; });
```
rendered via `<VideoView style={styles.videoPlayer} player={player} allowsFullscreen allowsPictureInPicture nativeControls />`.

Backend: `EngagementLog` model (`backend/content/models.py`) has `video_time_seconds` (existing, tab-dwell time — keep as is) — this task adds tracking for actual playback time as a NEW, separate metric, not a replacement.

## Requirement

### 1. Add a new field to track actual playback time
In `backend/content/models.py`, add to `EngagementLog`:
```python
video_watch_seconds = models.PositiveIntegerField(default=0, help_text="Actual video playback time (from pressing play to pausing/stopping), as opposed to video_time_seconds which measures time the Video tab was simply active/visible.")
```
Requires a migration.

Also update the corresponding admin display (`backend/content/admin.py`'s `EngagementLogAdmin` and the inline used on the participant stats page, `backend/participants/admin.py`'s stats view template context / `participant_stats.html`) to show this alongside the existing Video Time column — add a "Video Watch Time" column so both metrics are visible side by side. Follow the same `_fmt`-style mm:ss formatting pattern already used for the other time columns.

### 2. Update `log_engagement` view to accept the new field
`backend/content/views.py`'s `log_engagement` view currently accepts `video_time_seconds` (among others) and uses Django F() expressions to accumulate it. Add `video_watch_seconds` to the same accumulation pattern (extract from `request.data`, accumulate via F() expression, matching exactly how `video_time_seconds`/`audio_time_seconds`/`text_time_seconds` are currently handled).

### 3. Mobile: track actual playback time using the player's status
In `DailySessionScreen.js`, use `expo-video`'s player status to detect play/pause events and accumulate watch time separately from tab-dwell time.

`expo-video`'s player object supports a `statusChange` event (or you can poll `player.playing` — check the current `expo-video` version's API, likely via `useEvent(player, 'statusChange', ...)` from the `expo` package, or `player.addListener('statusChange', ...)` — use whichever pattern is idiomatic for the installed `expo-video` version, check its type definitions/docs if unsure).

**Logic needed:**
- Add a new ref, e.g. `videoWatchSecondsRef` (accumulator, similar pattern to `videoTimeRef`) and `playStartTimeRef` (timestamp of when playback last started, null when not playing).
- When the player's playing state changes to `true` (play pressed/resumed): set `playStartTimeRef.current = Date.now()`.
- When the player's playing state changes to `false` (paused, or video ends) OR when the component unmounts/tab changes away from Video: if `playStartTimeRef.current` is set, compute elapsed seconds since that timestamp, add to `videoWatchSecondsRef.current`, then clear `playStartTimeRef.current` to null (so we don't double-count).
- Make sure this cleanly handles: pressing play, pressing pause, pressing play again (resuming), switching away from the Video tab while playing (should stop the watch-time clock, same as a pause), and leaving the whole screen while playing (should also stop the clock, similar to the existing cleanup `useEffect` logic for `video_time_seconds`/`text_time_seconds`/etc.).
- Include `video_watch_seconds: videoWatchSecondsRef.current` in the `logEngagement(...)` call(s) that already send `video_time_seconds`, `audio_time_seconds` (wait — audio was removed in an earlier task, verify current state of that call before assuming its exact shape), `text_time_seconds`, `video_open_count`, etc. — same call sites, just one more field included.

### What NOT to change
- Do NOT remove or repurpose `video_time_seconds` — it continues to measure tab-dwell time exactly as before. `video_watch_seconds` is additive, a new complementary metric, not a replacement.
- Do NOT change how `video_open_count` is tracked — unrelated, unchanged.
- Do NOT change the Audio tab or audio tracking — audio tracking was already removed from the app in an earlier task; don't reintroduce it while working in this file.
- Do NOT change the VJ recording screen's or any other screen's playback tracking — this task is scoped to `DailySessionScreen.js`'s course video player only.

## Testing expectations
- Play a video for ~10 seconds, pause, confirm `video_watch_seconds` sent is approximately 10 (not more — shouldn't count time before play was pressed or after pause).
- Play, pause, play again (resume), pause again — confirm the two play segments correctly SUM together (e.g., 5 seconds + 7 seconds = 12 seconds total watch time), not overwritten or double-counted.
- Open the Video tab but never press play — confirm `video_watch_seconds` sent is 0, while `video_time_seconds` (tab-dwell) still correctly reflects time spent on the tab, proving the two metrics are genuinely independent.
- Start playing, then switch to the Text tab without pausing first — confirm the watch-time clock correctly stops (doesn't keep counting while on a different tab).
- Start playing, then leave the session screen entirely (navigate back) without pausing — confirm the accumulated watch time up to that point is still correctly sent (don't lose data on abrupt navigation away).
- Confirm the admin stats page and `EngagementLogAdmin` list view both show the new "Video Watch Time" column correctly formatted (mm:ss), alongside the existing "Video Time" column, for a real logged session.
- Run `python manage.py check` and confirm the migration applies cleanly.
