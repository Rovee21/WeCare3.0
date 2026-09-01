import io
import uuid
import boto3
from django.conf import settings


def _s3_client():
    return boto3.client(
        "s3",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )


def upload_audio_to_s3(file_bytes: bytes, content_type: str, participant, week: int) -> str:
    """Uploads a Voice Journal recording to the dedicated (private) audio bucket —
    separate from wecare-content, since these are participant health-related
    recordings, not publicly-readable curriculum media. Returns the S3 key (not a
    public URL); access is always via a short-lived presigned URL, see
    generate_audio_download_url."""
    if not settings.AWS_S3_VJ_AUDIO_BUCKET:
        raise RuntimeError("S3 not configured. Set AWS_S3_VJ_AUDIO_BUCKET in environment.")
    key = f"vj/{participant.participant_id}/week{week}/{uuid.uuid4()}.m4a"
    s3 = _s3_client()
    s3.upload_fileobj(
        io.BytesIO(file_bytes), settings.AWS_S3_VJ_AUDIO_BUCKET, key,
        ExtraArgs={"ContentType": content_type, "ServerSideEncryption": "AES256"},
    )
    return key


def generate_audio_download_url(audio_s3_key: str, expires: int = 600) -> str:
    if not settings.AWS_S3_VJ_AUDIO_BUCKET:
        raise RuntimeError("S3 not configured. Set AWS_S3_VJ_AUDIO_BUCKET in environment.")
    s3 = _s3_client()
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.AWS_S3_VJ_AUDIO_BUCKET, "Key": audio_s3_key},
        ExpiresIn=expires,
    )


def audio_download_url_for_entry(entry) -> str | None:
    """Shared by journal admin, the participants cross-participant dashboard, and the
    mobile history serializer: presigned URL for an S3-stored recording, falling back
    to the legacy local-disk file for entries recorded before this feature shipped."""
    if entry.audio_s3_key:
        return generate_audio_download_url(entry.audio_s3_key)
    if entry.audio_file:
        return entry.audio_file.url
    return None


def audio_filename_for_entry(entry) -> str:
    if entry.audio_s3_key:
        return entry.audio_s3_key.rsplit("/", 1)[-1]
    if entry.audio_file:
        return entry.audio_file.name.rsplit("/", 1)[-1]
    return "—"
