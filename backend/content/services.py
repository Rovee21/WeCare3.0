import uuid
import boto3
from django.conf import settings


def upload_video_to_s3(file, session) -> str:
    if not settings.AWS_S3_BUCKET:
        raise RuntimeError("S3 not configured. Set AWS_S3_BUCKET in environment.")
    key = f"curriculum/videos/w{session.week_number}/d{session.day_number}/{uuid.uuid4()}.mp4"
    s3 = boto3.client(
        "s3",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    s3.upload_fileobj(
        file, settings.AWS_S3_BUCKET, key,
        ExtraArgs={"ContentType": "video/mp4", "ServerSideEncryption": "AES256"},
    )
    return f"https://{settings.AWS_S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
