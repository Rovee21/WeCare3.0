from rest_framework import serializers
from .models import VoiceJournalEntry, VoiceJournalPrompt


class VoiceJournalPromptSerializer(serializers.ModelSerializer):
    class Meta:
        model = VoiceJournalPrompt
        fields = ["week_number", "prompt_en", "prompt_zh"]


class JournalPromptResponseSerializer(VoiceJournalPromptSerializer):
    already_submitted = serializers.BooleanField()

    class Meta(VoiceJournalPromptSerializer.Meta):
        fields = VoiceJournalPromptSerializer.Meta.fields + ["already_submitted"]


class UploadUrlResponseSerializer(serializers.Serializer):
    upload_url = serializers.URLField()
    s3_key = serializers.CharField()


class DirectUploadRequestSerializer(serializers.Serializer):
    audio = serializers.FileField()
    recording_seconds = serializers.IntegerField(required=False, default=0)
    emotion_label = serializers.CharField(required=False, allow_blank=True)
    vj_stress_level = serializers.IntegerField(min_value=1, max_value=10, required=False, allow_null=True)


class DirectUploadResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    week_number = serializers.IntegerField()
    recording_seconds = serializers.IntegerField()
    submitted_at = serializers.DateTimeField()


class VoiceJournalSubmitSerializer(serializers.Serializer):
    audio_s3_key = serializers.CharField(max_length=500)
    recording_seconds = serializers.IntegerField(min_value=0)
    vj_stress_level = serializers.IntegerField(min_value=1, max_value=10, required=False, allow_null=True)


class VoiceJournalEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = VoiceJournalEntry
        fields = [
            "id", "week_number", "recording_seconds",
            "vj_stress_level", "transcription_status", "submitted_at",
        ]
