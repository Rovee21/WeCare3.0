from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Session, ParticipantSession, EngagementLog
from .serializers import SessionSerializer, EngagementLogSerializer


def _get_participant(request):
    try:
        return request.user.participant
    except Exception:
        return None


def _filter_sessions_for_participant(participant):
    """Return sessions visible to this participant based on cohort targeting rules."""
    qs = Session.objects.filter(is_active=True)
    # For each cohort dimension: if target is set, it must match; if blank, it's universal
    filtered = []
    for session in qs.prefetch_related("resources"):
        g1_ok = not session.target_group1 or session.target_group1 == participant.group1
        g2_ok = not session.target_group2 or session.target_group2 == participant.group2
        g3_ok = not session.target_group3 or session.target_group3 == participant.group3
        if g1_ok and g2_ok and g3_ok:
            filtered.append(session)
    return filtered


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def session_list(request):
    participant = _get_participant(request)
    if not participant:
        return Response({"detail": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)
    sessions = _filter_sessions_for_participant(participant)
    serializer = SessionSerializer(sessions, many=True, context={"request": request})
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def session_today(request):
    participant = _get_participant(request)
    if not participant:
        return Response({"detail": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)

    week = participant.current_week_number
    sessions = _filter_sessions_for_participant(participant)

    # Today's session: current week, lowest unread day first; fallback to last of week
    week_sessions = [s for s in sessions if s.week_number == week]
    unread_ids = set(
        ParticipantSession.objects.filter(
            participant=participant, is_read=True
        ).values_list("session_id", flat=True)
    )
    unread = [s for s in week_sessions if s.id not in unread_ids]
    today = unread[0] if unread else (week_sessions[-1] if week_sessions else None)

    if not today:
        return Response({"detail": "No session available."}, status=status.HTTP_404_NOT_FOUND)
    return Response(SessionSerializer(today, context={"request": request}).data)


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


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def log_engagement(request):
    participant = _get_participant(request)
    if not participant:
        return Response({"detail": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = EngagementLogSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    EngagementLog.objects.create(participant=participant, **serializer.validated_data)
    return Response({"status": "ok"}, status=status.HTTP_201_CREATED)
