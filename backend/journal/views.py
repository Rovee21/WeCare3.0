import uuid
from django.conf import settings
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import VoiceJournalPrompt, VoiceJournalEntry
from .serializers import (
    VoiceJournalPromptSerializer,
    VoiceJournalSubmitSerializer,
    VoiceJournalEntrySerializer,
)

def _get_participant(request):
    try:
        return request.user.participant
    except Exception:
        return None


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def journal_prompt(request):
    participant = _get_participant(request)
    if not participant:
        return Response({"detail": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)

    week = participant.current_week_number
    try:
        prompt = VoiceJournalPrompt.objects.get(week_number=week)
    except VoiceJournalPrompt.DoesNotExist:
        return Response({"detail": "No prompt for this week."}, status=status.HTTP_404_NOT_FOUND)

    already_submitted = VoiceJournalEntry.objects.filter(
        participant=participant, week_number=week
    ).exists()

    return Response({
        **VoiceJournalPromptSerializer(prompt).data,
        "already_submitted": already_submitted,
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload_url(request):
    """Return a presigned S3 URL so the app can upload audio directly."""
    participant = _get_participant(request)
    if not participant:
        return Response({"detail": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)

    if not settings.AWS_S3_BUCKET:
        return Response(
            {"detail": "S3 not configured. Set AWS_S3_BUCKET in environment."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    import boto3
    week = participant.current_week_number
    s3_key = f"vj/{participant.participant_id}/week{week}/{uuid.uuid4()}.m4a"

    s3 = boto3.client(
        "s3",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    presigned_url = s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": settings.AWS_S3_BUCKET, "Key": s3_key, "ContentType": "audio/mp4"},
        ExpiresIn=600,  # 10 minutes
    )

    return Response({"upload_url": presigned_url, "s3_key": s3_key})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def submit_entry(request):
    """Called after the audio has been uploaded to S3."""
    participant = _get_participant(request)
    if not participant:
        return Response({"detail": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = VoiceJournalSubmitSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    week = participant.current_week_number

    # if VoiceJournalEntry.objects.filter(participant=participant, week_number=week).exists():
    #     return Response(
    #         {"detail": "You have already submitted a Voice Journal for this week."},
    #         status=status.HTTP_400_BAD_REQUEST,
    #     )

    entry = VoiceJournalEntry.objects.create(
        participant=participant,
        week_number=week,
        audio_s3_key=serializer.validated_data["audio_s3_key"],
        recording_seconds=serializer.validated_data["recording_seconds"],
        vj_stress_level=serializer.validated_data.get("vj_stress_level"),
    )

    _trigger_transcription(entry)

    return Response(VoiceJournalEntrySerializer(entry).data, status=status.HTTP_201_CREATED)


def _trigger_transcription(entry):
    """Start an AWS Transcribe job. Steps provided in setup guide if AWS not configured."""
    if not settings.AWS_S3_BUCKET:
        return

    try:
        import boto3
        transcribe = boto3.client(
            "transcribe",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        job_name = f"wecare-vj-{entry.pk}"
        media_uri = f"s3://{settings.AWS_S3_BUCKET}/{entry.audio_s3_key}"

        transcribe.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={"MediaFileUri": media_uri},
            MediaFormat="mp4",
            IdentifyLanguage=True,  # handles both EN and ZH recordings
            OutputBucketName=settings.AWS_TRANSCRIBE_OUTPUT_BUCKET or settings.AWS_S3_BUCKET,
            OutputKey=f"transcripts/{entry.pk}.json",
        )
        entry.transcription_status = VoiceJournalEntry.STATUS_PROCESSING
        entry.save(update_fields=["transcription_status"])
    except Exception:
        entry.transcription_status = VoiceJournalEntry.STATUS_FAILED
        entry.save(update_fields=["transcription_status"])

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def direct_upload(request):
    participant = _get_participant(request)
    if not participant:
        return Response({"detail": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)

    week = participant.current_week_number

    # if VoiceJournalEntry.objects.filter(participant=participant, week_number=week).exists():
    #     return Response(
    #         {"detail": "Already submitted for this week."},
    #         status=status.HTTP_400_BAD_REQUEST,
    #     )

    audio_file = request.FILES.get("audio")
    if not audio_file:
        return Response({"detail": "No audio file provided."}, status=status.HTTP_400_BAD_REQUEST)

    recording_seconds = int(request.data.get("recording_seconds", 0))
    emotion_label = request.data.get("emotion_label", "")
    vj_stress_level = request.data.get("vj_stress_level")
    if vj_stress_level:
        vj_stress_level = int(vj_stress_level)

    entry = VoiceJournalEntry.objects.create(
        participant=participant,
        week_number=week,
        audio_s3_key="",
        audio_file=audio_file,
        recording_seconds=recording_seconds,
        emotion_label=emotion_label,
        vj_stress_level=vj_stress_level,
    )

    return Response({
        "id": entry.id,
        "week_number": entry.week_number,
        "recording_seconds": entry.recording_seconds,
        "submitted_at": entry.submitted_at,
    }, status=status.HTTP_201_CREATED)