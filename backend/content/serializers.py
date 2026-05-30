from rest_framework import serializers
from .models import Session, AdditionalResource, EngagementLog


class AdditionalResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdditionalResource
        fields = ["id", "title", "title_zh", "resource_type", "url"]


class SessionSerializer(serializers.ModelSerializer):
    media_types = serializers.ReadOnlyField()
    week_label = serializers.ReadOnlyField()
    resources = AdditionalResourceSerializer(many=True, read_only=True)
    is_read = serializers.SerializerMethodField()

    class Meta:
        model = Session
        fields = [
            "id", "title", "title_zh", "week_number", "day_number",
            "week_label", "media_types",
            "video_url", "audio_url", "text_content", "text_content_zh",
            "resources", "is_read",
        ]

    def get_is_read(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        try:
            ps = obj.participantsession_set.get(participant=request.user.participant)
            return ps.is_read
        except Exception:
            return False


class EngagementLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = EngagementLog
        fields = [
            "course_title", "week_number",
            "video_open_count", "video_last_time",
            "read_count", "read_minutes",
            "interactive_feature_count", "interactive_feature_comment",
            "infographic_open_count", "tracking_download_count",
            "pushup_time", "push_up",
        ]
