from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
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


class VoiceJournalHistoryEntrySerializer(serializers.ModelSerializer):
    emotion_label = serializers.CharField(source="get_emotion_label_display")
    audio_url = serializers.SerializerMethodField()

    class Meta:
        model = VoiceJournalEntry
        fields = [
            "id", "week_number", "submitted_at",
            "emotion_label", "vj_stress_level", "recording_seconds", "audio_url",
        ]

    @extend_schema_field(serializers.URLField(allow_null=True))
    def get_audio_url(self, obj):
        if not obj.audio_file:
            return None
        request = self.context.get("request")
        url = obj.audio_file.url
        return request.build_absolute_uri(url) if request else url
