from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
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
    status = serializers.SerializerMethodField()
    locked = serializers.SerializerMethodField()

    class Meta:
        model = Session
        fields = [
            "id", "title", "title_zh", "week_number", "day_number",
            "week_label", "media_types",
            "video_url", "audio_url", "text_content", "text_content_zh",
            "resources", "is_read", "status", "locked",
        ]

    def _participant_session(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        if not hasattr(self, "_ps_cache"):
            self._ps_cache = {}
        if obj.id not in self._ps_cache:
            try:
                self._ps_cache[obj.id] = obj.participantsession_set.get(participant=request.user.participant)
            except Exception:
                self._ps_cache[obj.id] = None
        return self._ps_cache[obj.id]

    @extend_schema_field(serializers.BooleanField)
    def get_is_read(self, obj):
        ps = self._participant_session(obj)
        return bool(ps and ps.is_read)

    @extend_schema_field(serializers.ChoiceField(choices=["not_started", "in_progress", "completed"]))
    def get_status(self, obj):
        ps = self._participant_session(obj)
        if not ps:
            return "not_started"
        if ps.is_read:
            return "completed"
        if ps.started_at:
            return "in_progress"
        return "not_started"

    @extend_schema_field(serializers.BooleanField)
    def get_locked(self, obj):
        return getattr(obj, "locked", False)


class StatusResponseSerializer(serializers.Serializer):
    status = serializers.CharField()


class EngagementLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = EngagementLog
        fields = [
            "session_id",
            "course_title", "week_number",
            "video_open_count", "video_last_time",
            "video_time_seconds", "video_watch_seconds", "audio_time_seconds", "text_time_seconds",
            "read_count", "read_minutes",
            "interactive_feature_count", "interactive_feature_comment",
            "infographic_open_count", "tracking_download_count",
            "pushup_time", "push_up",
        ]