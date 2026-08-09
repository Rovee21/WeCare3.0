from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from .models import Session, ParticipantSession, EngagementLog, SessionOverride
from .serializers import SessionSerializer, EngagementLogSerializer, StatusResponseSerializer


def _get_participant(request):
    try:
        return request.user.participant
    except Exception:
        return None


def _filter_sessions_for_participant(participant):
    """Return sessions visible to this participant, applying cohort targeting and then
    date-based scheduling on top: future weeks are omitted entirely, past/completed weeks
    are always fully visible, and within the current effective week a session is flagged
    `locked` unless it passes the calendar-day gate AND every lower-day_number session in
    that same week (for this participant's cohort) is already read — days must be
    completed in order, regardless of how much calendar time has passed. An admin-set
    SessionOverride takes priority over the day/sequential gate, but only within the
    current effective week — it can't reach into past weeks (already unconditionally
    unlocked) or future weeks (not shown at all). A waitlisted participant (their cohort's
    program_start_date hasn't arrived yet, or isn't set at all) sees no sessions at all."""
    if participant.is_waitlisted():
        return []

    qs = Session.objects.filter(is_active=True)
    effective_week = participant.effective_current_week()
    unlocked_day = participant.unlocked_day_number()
    read_ids = set(
        ParticipantSession.objects.filter(participant=participant, is_read=True)
        .values_list("session_id", flat=True)
    )
    overrides = dict(
        SessionOverride.objects.filter(participant=participant)
        .values_list("session_id", "override_type")
    )

    # For each cohort dimension: if target is set, it must match; if blank, it's universal
    filtered = []
    prior_days_read = True  # tracks lower day_numbers seen so far within the current week
    for session in qs.prefetch_related("resources"):
        g1_ok = not session.target_group1 or session.target_group1 == participant.group1
        g2_ok = not session.target_group2 or session.target_group2 == participant.group2
        g3_ok = not session.target_group3 or session.target_group3 == participant.group3
        if not (g1_ok and g2_ok and g3_ok):
            continue

        if session.week_number > effective_week:
            continue

        if session.week_number == effective_week:
            override = overrides.get(session.id)
            if override == SessionOverride.OVERRIDE_UNLOCK:
                session.locked = False
            elif override == SessionOverride.OVERRIDE_LOCK:
                session.locked = True
            else:
                calendar_unlocked = session.day_number <= unlocked_day
                session.locked = not (calendar_unlocked and prior_days_read)
            if session.id not in read_ids:
                prior_days_read = False
        else:
            session.locked = False

        filtered.append(session)
    return filtered


@extend_schema(responses=SessionSerializer(many=True))
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def session_list(request):
    participant = _get_participant(request)
    if not participant:
        return Response({"detail": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)
    sessions = _filter_sessions_for_participant(participant)
    serializer = SessionSerializer(sessions, many=True, context={"request": request})
    return Response(serializer.data)


@extend_schema(responses=SessionSerializer)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def session_today(request):
    participant = _get_participant(request)
    if not participant:
        return Response({"detail": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)

    week = participant.current_week_number
    sessions = _filter_sessions_for_participant(participant)

    # Today's session: current week, lowest unread day first; fallback to last of week
    read_ids = set(
        ParticipantSession.objects.filter(
            participant=participant, is_read=True
        ).values_list("session_id", flat=True)
    )

    # Find first unread, unlocked session across all weeks
    unread = [s for s in sessions if s.id not in read_ids and not getattr(s, "locked", False)]
    today = unread[0] if unread else None

    if not today:
        return Response({"detail": "No session available."}, status=status.HTTP_404_NOT_FOUND)
    return Response(SessionSerializer(today, context={"request": request}).data)


@extend_schema(request=None, responses=StatusResponseSerializer)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_read(request, session_id):
    participant = _get_participant(request)
    if not participant:
        return Response({"detail": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)
    try:
        session = Session.objects.get(pk=session_id)
    except Session.DoesNotExist:
        return Response({"detail": "Session not found."}, status=status.HTTP_404_NOT_FOUND)

    ps, _ = ParticipantSession.objects.get_or_create(participant=participant, session=session)
    if not ps.is_read:
        ps.is_read = True
        ps.read_at = timezone.now()
        ps.save(update_fields=["is_read", "read_at"])

    return Response({"status": "ok"})


@extend_schema(request=EngagementLogSerializer, responses=StatusResponseSerializer)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def log_engagement(request):
    participant = _get_participant(request)
    if not participant:
        return Response({"detail": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)

    session_id = request.data.get("session_id")
    session = None
    if session_id:
        try:
            session = Session.objects.get(pk=session_id)
        except Session.DoesNotExist:
            pass

    defaults = {
        "course_title": request.data.get("course_title", ""),
        "week_number": request.data.get("week_number"),
    }

    log, created = EngagementLog.objects.get_or_create(
        participant=participant,
        session=session,
        defaults=defaults,
    )

    from django.db.models import F
    update_fields = []

    video_time = int(request.data.get("video_time_seconds", 0))
    video_watch = int(request.data.get("video_watch_seconds", 0))
    audio_time = int(request.data.get("audio_time_seconds", 0))
    text_time  = int(request.data.get("text_time_seconds", 0))
    video_opens = int(request.data.get("video_open_count", 0))
    emoji_taps  = int(request.data.get("interactive_feature_count", 0))

    if video_time:
        log.video_time_seconds = F("video_time_seconds") + video_time
        update_fields.append("video_time_seconds")
    if video_watch:
        log.video_watch_seconds = F("video_watch_seconds") + video_watch
        update_fields.append("video_watch_seconds")
    if audio_time:
        log.audio_time_seconds = F("audio_time_seconds") + audio_time
        update_fields.append("audio_time_seconds")
    if text_time:
        log.text_time_seconds = F("text_time_seconds") + text_time
        update_fields.append("text_time_seconds")
    if video_opens:
        log.video_open_count = F("video_open_count") + video_opens
        update_fields.append("video_open_count")
    if emoji_taps:
        log.interactive_feature_count = F("interactive_feature_count") + emoji_taps
        update_fields.append("interactive_feature_count")

    if update_fields:
        log.save(update_fields=update_fields)

    return Response({"status": "ok"}, status=status.HTTP_200_OK)
