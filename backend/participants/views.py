from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from .models import Participant
from .serializers import EnrollSerializer, ParticipantProfileSerializer


@api_view(["POST"])
@permission_classes([AllowAny])
def enroll(request):
    serializer = EnrollSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    code = serializer.validated_data["code"].strip().upper()

    try:
        participant = Participant.objects.get(enrollment_code=code, is_enrolled=False)
    except Participant.DoesNotExist:
        return Response(
            {"detail": "Invalid or already used enrollment code."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    username = f"participant_{participant.pk}"
    user, _ = User.objects.get_or_create(username=username)
    user.email = participant.email
    user.save()

    participant.user = user
    participant.is_enrolled = True
    participant.enrolled_at = timezone.now()
    participant.enrollment_code = None  # single-use: invalidate immediately
    participant.save(update_fields=["user", "is_enrolled", "enrolled_at", "enrollment_code"])

    token, _ = Token.objects.get_or_create(user=user)

    return Response({
        "token": token.key,
        "language": participant.language,
        "participant_id": participant.participant_id,
        "week_number": participant.current_week_number,
        "group1": participant.group1,
        "group2": participant.group2,
        "group3": participant.group3,
        "adrd_relationship_group": participant.adrd_relationship_group,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def profile(request):
    try:
        participant = request.user.participant
    except Participant.DoesNotExist:
        return Response({"detail": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)
    return Response(ParticipantProfileSerializer(participant).data)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_account(request):
    # Deleting the User cascades to the Token and Participant
    request.user.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
