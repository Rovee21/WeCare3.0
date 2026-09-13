from pathlib import Path
from types import SimpleNamespace
from django import forms
from django.contrib import admin
from django.template.response import TemplateResponse
from django.utils.html import format_html
from .models import (
    Session, AdditionalResource, EngagementLog, NotificationLog, ParticipantSession,
    DailyNotificationSettings, MediaAsset,
)
from .services import (
    convert_docx_to_html, upload_image_to_s3, upload_media_asset_to_s3,
    create_or_replace_media_asset,
)


_MEDIA_ASSET_VALIDATION = {
    MediaAsset.TYPE_VIDEO: (("video/mp4",), (".mp4",), "Please upload an MP4 video file."),
    MediaAsset.TYPE_PDF: (("application/pdf",), (".pdf",), "Please upload a PDF file."),
    MediaAsset.TYPE_AUDIO: (
        ("audio/mpeg", "audio/mp4", "audio/x-m4a"), (".mp3", ".m4a"),
        "Please upload an MP3 or M4A audio file.",
    ),
    MediaAsset.TYPE_DOCUMENT: (
        ("application/vnd.openxmlformats-officedocument.wordprocessingml.document",),
        (".docx",), "Please upload a .docx Word document.",
    ),
    MediaAsset.TYPE_IMAGE: (
        ("image/jpeg", "image/png"), (".jpg", ".jpeg", ".png"),
        "Please upload a JPG or PNG image.",
    ),
}

# Bulk-upload extension -> asset_type inference (see MediaAssetAdmin.bulk_upload_view).
_EXT_TO_ASSET_TYPE = {
    ".mp4": MediaAsset.TYPE_VIDEO,
    ".pdf": MediaAsset.TYPE_PDF,
    ".mp3": MediaAsset.TYPE_AUDIO,
    ".m4a": MediaAsset.TYPE_AUDIO,
    ".docx": MediaAsset.TYPE_DOCUMENT,
    ".jpg": MediaAsset.TYPE_IMAGE,
    ".jpeg": MediaAsset.TYPE_IMAGE,
    ".png": MediaAsset.TYPE_IMAGE,
}


class MediaAssetAdminForm(forms.ModelForm):
    file_upload = forms.FileField(
        required=False,
        label="Upload file",
        help_text="Uploads directly to S3 and fills in File URL below. Pick the matching "
                   "Type above before uploading. Required when creating a new asset.",
    )
    replace_existing = forms.BooleanField(
        required=False,
        label="Replace existing asset with this title/type",
        help_text="If an asset with this exact title and type already exists, check this "
                   "to overwrite it in place — any session/resource already using it picks "
                   "up the new file automatically, no re-pick needed. Leave unchecked to "
                   "be stopped instead of accidentally creating a duplicate.",
    )

    class Meta:
        model = MediaAsset
        fields = ["title", "asset_type", "file_upload", "replace_existing", "file_url", "html_content"]

    def clean(self):
        cleaned_data = super().clean()
        f = cleaned_data.get("file_upload")
        asset_type = cleaned_data.get("asset_type")
        title = cleaned_data.get("title")
        if not self.instance.pk and not f:
            raise forms.ValidationError("Please upload a file.")
        if f and asset_type:
            content_types, exts, error = _MEDIA_ASSET_VALIDATION[asset_type]
            if not (f.content_type in content_types or f.name.lower().endswith(exts)):
                raise forms.ValidationError(error)
        if not self.instance.pk and title and asset_type:
            dup = MediaAsset.objects.filter(title=title, asset_type=asset_type).exists()
            if dup and not cleaned_data.get("replace_existing"):
                raise forms.ValidationError(
                    f"An asset named \"{title}\" ({asset_type}) already exists. Check "
                    "\"Replace existing asset with this title/type\" below to overwrite "
                    "it, or change the title to upload this as a separate new asset."
                )
        return cleaned_data


# FK fields elsewhere in this app that point at MediaAsset (all related_name="+", so no
# reverse accessor exists to introspect this list automatically — keep in sync with
# models.py if a new asset-picker field is ever added).
_SESSION_ASSET_FIELDS = [
    "video_asset", "video_asset_zh", "text_pdf_asset", "text_pdf_asset_zh",
    "docx_asset", "docx_asset_zh",
]


def _media_asset_usage_labels(asset):
    """Human-readable descriptions of every Session/AdditionalResource currently
    pointing at this asset, or [] if it's unused. Used to block deletion of an
    in-use asset rather than silently unlinking it (SET_NULL) and destroying its S3
    file out from under a live session."""
    labels = []
    for field in _SESSION_ASSET_FIELDS:
        for s in Session.objects.filter(**{field: asset}):
            labels.append(f'Session "{s}" ({field})')
    for r in AdditionalResource.objects.filter(media_asset=asset).select_related("session"):
        labels.append(f'Additional Resource "{r.title}" on Session "{r.session}"')
    return labels


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    form = MediaAssetAdminForm
    list_display = ["title", "asset_type", "uploaded_at"]
    list_filter = ["asset_type"]
    search_fields = ["title"]

    def has_delete_permission(self, request, obj=None):
        # Blocks both the single-object delete view (raises PermissionDenied there,
        # caught and turned into a friendly message by delete_view below) and the
        # changelist's "Delete selected" bulk action (Django's built-in delete_selected
        # aborts the whole batch if any selected object fails this check).
        if obj is not None and _media_asset_usage_labels(obj):
            return False
        return super().has_delete_permission(request, obj)

    def delete_view(self, request, object_id, extra_context=None):
        from django.contrib import messages
        from django.shortcuts import redirect

        obj = self.get_object(request, object_id)
        if obj is not None:
            labels = _media_asset_usage_labels(obj)
            if labels:
                self.message_user(
                    request,
                    f'Cannot delete "{obj}" — it\'s still in use by: {"; ".join(labels)}. '
                    "Unlink it there first (pick a different asset, upload a replacement, "
                    "or clear the field), then delete it.",
                    level=messages.ERROR,
                )
                return redirect(f"/admin/content/mediaasset/{object_id}/change/")
        return super().delete_view(request, object_id, extra_context)

    def get_fields(self, request, obj=None):
        if obj is not None:
            return ["title", "asset_type", "file_url"]
        return ["title", "asset_type", "file_upload", "replace_existing", "file_url"]

    def save_model(self, request, obj, form, change):
        if change:
            obj.save()
            return
        # clean() already blocks the unconfirmed-duplicate case, so this only ever
        # returns "created" or "replaced" here.
        asset, status = create_or_replace_media_asset(
            obj.title, obj.asset_type,
            form.cleaned_data.get("file_upload"), form.cleaned_data.get("replace_existing"),
        )
        obj.pk = asset.pk
        obj.file_url = asset.file_url
        obj.html_content = asset.html_content
        obj.original_filename = asset.original_filename
        obj.uploaded_at = asset.uploaded_at
        if status == "replaced":
            self.message_user(request, f'Replaced the existing "{asset.title}" ({asset.asset_type}) asset with this upload.')

    def get_readonly_fields(self, request, obj=None):
        # An asset's file/type is set once at upload time — to replace it, upload a
        # new asset rather than mutating one that other sessions/resources may
        # already be pointing at. Title stays editable so a typo can still be fixed.
        if obj is not None:
            return ["asset_type", "file_url"]
        return ["file_url"]

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom = [
            path(
                "bulk-upload/",
                self.admin_site.admin_view(self.bulk_upload_view),
                name="content_mediaasset_bulk_upload",
            ),
        ]
        return custom + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["bulk_upload_url"] = "/admin/content/mediaasset/bulk-upload/"
        return super().changelist_view(request, extra_context)

    def bulk_upload_view(self, request):
        results = []
        if request.method == "POST":
            replace_existing = request.POST.get("replace_existing") == "on"
            for f in request.FILES.getlist("files"):
                filename = f.name
                ext = Path(filename).suffix.lower()
                asset_type = _EXT_TO_ASSET_TYPE.get(ext)
                if not asset_type:
                    results.append({"filename": filename, "status": "error", "error": f"Unsupported file type ({ext or 'no extension'})"})
                    continue
                title = Path(filename).stem
                try:
                    asset, status = create_or_replace_media_asset(title, asset_type, f, replace_existing)
                    if status == "skipped_duplicate":
                        results.append({
                            "filename": filename, "status": "skipped",
                            "error": f'An asset named "{title}" ({asset_type}) already exists — not uploaded. '
                                     'Check "Replace existing duplicates" above and re-upload to overwrite it.',
                        })
                    else:
                        results.append({"filename": filename, "status": status, "asset_type": asset_type})
                except Exception as e:
                    results.append({"filename": filename, "status": "error", "error": str(e)})

        context = {
            **self.admin_site.each_context(request),
            "title": "Bulk Upload Media Assets",
            "results": results,
        }
        return TemplateResponse(request, "admin/content/mediaasset/bulk_upload.html", context)


class AdditionalResourceInlineForm(forms.ModelForm):
    url = forms.URLField(
        required=False,
        help_text="Paste a link (Article/Video/website), or leave blank and use the "
                   "PDF upload/library fields instead.",
    )
    pdf_upload = forms.FileField(
        required=False,
        label="Upload PDF",
        help_text="Uploads directly to S3 and adds it to the Media Library, or pick an "
                   "already-uploaded one below instead.",
    )

    class Meta:
        model = AdditionalResource
        fields = ["title", "title_zh", "resource_type", "media_asset", "pdf_upload", "url"]

    def clean_pdf_upload(self):
        f = self.cleaned_data.get("pdf_upload")
        if f and not (f.content_type == "application/pdf" or f.name.lower().endswith(".pdf")):
            raise forms.ValidationError("Please upload a PDF file.")
        return f

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("url") and not cleaned_data.get("pdf_upload") and not cleaned_data.get("media_asset"):
            raise forms.ValidationError("Provide a URL, a PDF upload, or pick a Media Library asset.")
        return cleaned_data


class AdditionalResourceInline(admin.TabularInline):
    model = AdditionalResource
    form = AdditionalResourceInlineForm
    extra = 1
    fields = ["title", "title_zh", "resource_type", "media_asset", "pdf_upload", "url"]
    autocomplete_fields = ["media_asset"]


class SessionAdminForm(forms.ModelForm):
    video_upload = forms.FileField(
        required=False,
        label="Upload MP4 video",
        help_text="Uploads directly to S3 and fills in Video URL below.",
    )
    video_upload_zh = forms.FileField(
        required=False,
        label="Upload MP4 video (Chinese)",
        help_text="Same as above, populates the Chinese Video URL field. If left blank, "
                   "Mandarin-selected participants will see a 'not yet translated' message "
                   "in place of a video, instead of the English one.",
    )
    docx_upload = forms.FileField(
        required=False,
        label="Upload Word document (English)",
        help_text="Uploads a .docx, converts it to rich text (headings/formatting, with "
                   "inline images extracted and uploaded to S3), and fills in the HTML "
                   "field below. The result can still be hand-edited afterward, same as "
                   "Video URL after an MP4 upload.",
    )
    docx_upload_zh = forms.FileField(
        required=False,
        label="Upload Word document (Chinese)",
        help_text="Same as above, populates the Chinese HTML field below.",
    )
    text_pdf_upload = forms.FileField(
        required=False,
        label="Upload PDF for Text section",
        help_text="Uploads directly to S3 and fills in Text PDF URL below. When set, the "
                   "app shows this PDF in an in-app viewer for the Text tab instead of the "
                   "Word-doc-derived HTML above.",
    )
    text_pdf_upload_zh = forms.FileField(
        required=False,
        label="Upload PDF for Text section (Chinese)",
        help_text="Same as above, populates the Chinese Text PDF URL field.",
    )

    class Meta:
        model = Session
        fields = "__all__"

    def _clean_video(self, field_name):
        f = self.cleaned_data.get(field_name)
        if f and not (f.content_type == "video/mp4" or f.name.lower().endswith(".mp4")):
            raise forms.ValidationError("Please upload an MP4 video file.")
        return f

    def clean_video_upload(self):
        return self._clean_video("video_upload")

    def clean_video_upload_zh(self):
        return self._clean_video("video_upload_zh")

    def _clean_docx(self, field_name):
        f = self.cleaned_data.get(field_name)
        docx_mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if f and not (f.content_type == docx_mime or f.name.lower().endswith(".docx")):
            raise forms.ValidationError("Please upload a .docx Word document.")
        return f

    def clean_docx_upload(self):
        return self._clean_docx("docx_upload")

    def clean_docx_upload_zh(self):
        return self._clean_docx("docx_upload_zh")

    def _clean_text_pdf(self, field_name):
        f = self.cleaned_data.get(field_name)
        if f and not (f.content_type == "application/pdf" or f.name.lower().endswith(".pdf")):
            raise forms.ValidationError("Please upload a PDF file.")
        return f

    def clean_text_pdf_upload(self):
        return self._clean_text_pdf("text_pdf_upload")

    def clean_text_pdf_upload_zh(self):
        return self._clean_text_pdf("text_pdf_upload_zh")

    def clean(self):
        cleaned_data = super().clean()
        week = cleaned_data.get("week_number")
        day = cleaned_data.get("day_number")

        upload = cleaned_data.get("video_upload")
        if upload:
            try:
                cleaned_data["video_asset"] = MediaAsset.objects.create(
                    title=f"{cleaned_data.get('title') or 'Untitled'} — video",
                    asset_type=MediaAsset.TYPE_VIDEO,
                    file_url=upload_media_asset_to_s3(upload, MediaAsset.TYPE_VIDEO),
                    original_filename=upload.name,
                )
            except Exception as e:
                raise forms.ValidationError(f"Video upload failed: {e}")

        upload_zh = cleaned_data.get("video_upload_zh")
        if upload_zh:
            try:
                cleaned_data["video_asset_zh"] = MediaAsset.objects.create(
                    title=f"{cleaned_data.get('title') or 'Untitled'} — video (Chinese)",
                    asset_type=MediaAsset.TYPE_VIDEO,
                    file_url=upload_media_asset_to_s3(upload_zh, MediaAsset.TYPE_VIDEO),
                    original_filename=upload_zh.name,
                )
            except Exception as e:
                raise forms.ValidationError(f"Video upload (Chinese) failed: {e}")

        # Picking a Word Document asset from the library copies its HTML in once, at
        # the moment the pick actually changes — it does not stay dynamically linked,
        # so the field remains freely hand-editable afterward (same as after a fresh
        # docx upload). Comparing against self.instance's still-unmutated saved value
        # (construct_instance() hasn't run yet at this point in clean()) is essential:
        # without it, resaving a session that already has a docx_asset linked would
        # silently overwrite any hand-edit back to the library's original HTML on every
        # subsequent save, since the same asset id gets resubmitted every time the form
        # re-renders. A fresh upload in the same submission (below) always overrides.
        docx_asset = cleaned_data.get("docx_asset")
        if docx_asset and docx_asset.pk != self.instance.docx_asset_id:
            cleaned_data["text_content_html"] = docx_asset.html_content

        docx_asset_zh = cleaned_data.get("docx_asset_zh")
        if docx_asset_zh and docx_asset_zh.pk != self.instance.docx_asset_zh_id:
            cleaned_data["text_content_html_zh"] = docx_asset_zh.html_content

        docx = cleaned_data.get("docx_upload")
        if docx and week is not None and day is not None:
            try:
                cleaned_data["text_content_html"] = convert_docx_to_html(
                    docx, lambda data, ct: upload_image_to_s3(data, ct, SimpleNamespace(week_number=week, day_number=day))
                )
            except Exception as e:
                raise forms.ValidationError(f"Word document (English) conversion failed: {e}")

        docx_zh = cleaned_data.get("docx_upload_zh")
        if docx_zh and week is not None and day is not None:
            try:
                cleaned_data["text_content_html_zh"] = convert_docx_to_html(
                    docx_zh, lambda data, ct: upload_image_to_s3(data, ct, SimpleNamespace(week_number=week, day_number=day))
                )
            except Exception as e:
                raise forms.ValidationError(f"Word document (Chinese) conversion failed: {e}")

        text_pdf = cleaned_data.get("text_pdf_upload")
        if text_pdf:
            try:
                cleaned_data["text_pdf_asset"] = MediaAsset.objects.create(
                    title=f"{cleaned_data.get('title') or 'Untitled'} — text PDF",
                    asset_type=MediaAsset.TYPE_PDF,
                    file_url=upload_media_asset_to_s3(text_pdf, MediaAsset.TYPE_PDF),
                    original_filename=text_pdf.name,
                )
            except Exception as e:
                raise forms.ValidationError(f"Text PDF upload failed: {e}")

        text_pdf_zh = cleaned_data.get("text_pdf_upload_zh")
        if text_pdf_zh:
            try:
                cleaned_data["text_pdf_asset_zh"] = MediaAsset.objects.create(
                    title=f"{cleaned_data.get('title') or 'Untitled'} — text PDF (Chinese)",
                    asset_type=MediaAsset.TYPE_PDF,
                    file_url=upload_media_asset_to_s3(text_pdf_zh, MediaAsset.TYPE_PDF),
                    original_filename=text_pdf_zh.name,
                )
            except Exception as e:
                raise forms.ValidationError(f"Text PDF (Chinese) upload failed: {e}")

        return cleaned_data


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    form = SessionAdminForm
    list_display = [
        "week_number", "day_number", "title",
        "target_group1_display", "target_group2_display", "target_group3_display",
        "target_relationship_display",
        "is_active",
    ]
    list_filter = [
        "week_number", "target_group1", "target_group2", "target_group3",
        "target_relationship", "is_active",
    ]
    search_fields = ["title", "title_zh"]
    inlines = [AdditionalResourceInline]
    list_per_page = 50
    autocomplete_fields = [
        "video_asset", "video_asset_zh", "text_pdf_asset", "text_pdf_asset_zh",
        "docx_asset", "docx_asset_zh",
    ]

    fieldsets = (
        ("Identity", {
            "fields": ("week_number", "day_number", "title", "title_zh", "is_active"),
        }),
        ("Cohort Targeting", {
            "fields": ("target_group1", "target_group2", "target_group3", "target_relationship"),
            "description": "Leave blank to show this session to all participants in that dimension.",
        }),
        ("Media URLs", {
            "fields": (
                "video_upload", "video_asset", "video_url",
                "video_upload_zh", "video_asset_zh", "video_url_zh",
            ),
            "classes": ("wide",),
            "description": "Upload a new MP4, or pick an already-uploaded one from the Media "
                            "Library below — either way it takes priority over the legacy Video "
                            "URL field, which stays as a fallback for old sessions and pasted "
                            "external links. Upload/pick a separate Chinese video below — if "
                            "left blank, Mandarin-selected participants see a placeholder "
                            "instead of the English video.",
        }),
        ("Text Content", {
            "fields": (
                "docx_upload", "docx_asset", "text_content_html",
                "docx_upload_zh", "docx_asset_zh", "text_content_html_zh",
                "text_pdf_upload", "text_pdf_asset", "text_content_pdf_url",
                "text_pdf_upload_zh", "text_pdf_asset_zh", "text_content_pdf_url_zh",
                "text_content", "text_content_zh",
            ),
            "classes": ("wide",),
            "description": "Upload a .docx (or pick one from the Media Library) to auto-fill "
                            "the HTML field directly below it — embedded images are extracted "
                            "and hosted on S3 automatically, in reading order. Either way, you "
                            "can hand-edit the resulting HTML afterward — picking an asset only "
                            "copies its HTML in once, it doesn't stay linked. Alternatively, "
                            "upload a new PDF or pick one from the Media Library below — when a "
                            "Text PDF is set (via either path), the app shows it in an in-app "
                            "viewer for the Text tab instead of the HTML above. The plain-text "
                            "fields below remain a fallback used by older sessions/app versions "
                            "with no rich content.",
        }),
    )

    def save_formset(self, request, form, formset, change):
        if formset.model is AdditionalResource:
            for f in formset.forms:
                pdf = f.cleaned_data.get("pdf_upload") if f.cleaned_data else None
                if pdf:
                    f.instance.media_asset = MediaAsset.objects.create(
                        title=f.cleaned_data.get("title") or "Untitled",
                        asset_type=MediaAsset.TYPE_PDF,
                        file_url=upload_media_asset_to_s3(pdf, MediaAsset.TYPE_PDF),
                        original_filename=pdf.name,
                    )
        formset.save()

    def target_group1_display(self, obj):
        if not obj.target_group1:
            return format_html('<span style="color:#999;">All</span>')
        return obj.get_target_group1_display()
    target_group1_display.short_description = "Group 1 (Intervention/Control)"
    target_group1_display.admin_order_field = "target_group1"

    def target_group2_display(self, obj):
        if not obj.target_group2:
            return format_html('<span style="color:#999;">All</span>')
        return obj.get_target_group2_display()
    target_group2_display.short_description = "Group 2 (Mild/Moderate/Severe)"
    target_group2_display.admin_order_field = "target_group2"

    def target_group3_display(self, obj):
        if not obj.target_group3:
            return format_html('<span style="color:#999;">All</span>')
        return obj.get_target_group3_display()
    target_group3_display.short_description = "Group 3 (High/Low Stress)"
    target_group3_display.admin_order_field = "target_group3"

    def target_relationship_display(self, obj):
        if not obj.target_relationship:
            return format_html('<span style="color:#999;">All</span>')
        return obj.get_target_relationship_display()
    target_relationship_display.short_description = "Relationship Target"
    target_relationship_display.admin_order_field = "target_relationship"


@admin.register(EngagementLog)
class EngagementLogAdmin(admin.ModelAdmin):
    list_display = [
        "participant_label", "course_title", "week_number",
        "total_time", "video_time", "video_watch_time", "text_time",
        "video_open_count", "emoji_taps", "logged_at",
    ]
    list_filter = ["week_number", "logged_at"]
    search_fields = ["participant__email", "course_title"]
    date_hierarchy = "logged_at"
    list_per_page = 100
    readonly_fields = [f.name for f in EngagementLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def participant_label(self, obj):
        return obj.participant.participant_id if obj.participant else "—"
    participant_label.short_description = "Participant"

    def _fmt_time(self, seconds):
        if not seconds:
            return format_html('<span style="color:#999;">—</span>')
        m, s = divmod(seconds, 60)
        return f"{m}:{s:02d}"

    def total_time(self, obj):
        total = obj.video_time_seconds + obj.text_time_seconds
        return self._fmt_time(total)
    total_time.short_description = "Total Time"

    def video_time(self, obj):
        return self._fmt_time(obj.video_time_seconds)
    video_time.short_description = "Video Time"

    def video_watch_time(self, obj):
        return self._fmt_time(obj.video_watch_seconds)
    video_watch_time.short_description = "Video Watch Time"

    def text_time(self, obj):
        return self._fmt_time(obj.text_time_seconds)
    text_time.short_description = "Text Time"

    def emoji_taps(self, obj):
        if not obj.interactive_feature_count:
            return format_html('<span style="color:#999;">—</span>')
        return obj.interactive_feature_count
    emoji_taps.short_description = "Emoji Taps"


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = [
        "participant_label", "notification_type", "title", "push_up", "status",
        "scheduled_for", "sent_at", "actually_sent_at", "opened_at", "was_opened",
    ]
    list_filter = ["notification_type", "status", "sent_at"]
    search_fields = ["participant__email", "title", "push_up"]
    date_hierarchy = "sent_at"
    list_per_page = 100
    readonly_fields = [f.name for f in NotificationLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def participant_label(self, obj):
        return obj.participant.participant_id if obj.participant else "—"
    participant_label.short_description = "Participant"
    participant_label.admin_order_field = "participant__email"

    def was_opened(self, obj):
        if obj.opened_at:
            return format_html('<span style="color:#2e7d32;">✓ Opened</span>')
        return format_html('<span style="color:#e53935;">Not opened</span>')
    was_opened.short_description = "Opened?"


@admin.register(DailyNotificationSettings)
class DailyNotificationSettingsAdmin(admin.ModelAdmin):
    """Singleton settings — only one row should ever exist. Adding is blocked once a
    row exists, and deleting is blocked outright so there's always exactly one to edit."""
    list_display = ["send_time", "title", "body", "is_enabled", "updated_at"]
    fields = ["send_time", "title", "body", "is_enabled", "last_sent_date"]
    readonly_fields = ["last_sent_date"]

    def has_add_permission(self, request):
        return not DailyNotificationSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        # Skip straight to the (only) row's edit form instead of a list view of one item.
        settings_obj, _ = DailyNotificationSettings.objects.get_or_create()
        from django.shortcuts import redirect
        return redirect("admin:content_dailynotificationsettings_change", settings_obj.pk)

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom = [
            path(
                "<int:object_id>/reset-last-sent/",
                self.admin_site.admin_view(self.reset_last_sent_view),
                name="content_dailynotificationsettings_reset_last_sent",
            ),
        ]
        return custom + urls

    def reset_last_sent_view(self, request, object_id):
        from django.shortcuts import redirect, get_object_or_404
        settings_obj = get_object_or_404(DailyNotificationSettings, pk=object_id)
        settings_obj.last_sent_date = None
        settings_obj.save(update_fields=["last_sent_date"])
        self.message_user(
            request,
            "Reset — the daily notification can now send again today. "
            "This does not send anything itself; it only clears the "
            "\"already sent today\" flag for the next scheduled check-in.",
        )
        return redirect("admin:content_dailynotificationsettings_change", object_id)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["reset_last_sent_url"] = f"/admin/content/dailynotificationsettings/{object_id}/reset-last-sent/"
        return super().change_view(request, object_id, form_url, extra_context)
