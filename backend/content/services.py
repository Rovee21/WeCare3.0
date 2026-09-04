import io
import uuid
import boto3
import mammoth
import nh3
from django.conf import settings


def _s3_client():
    return boto3.client(
        "s3",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )


def upload_video_to_s3(file, session) -> str:
    if not settings.AWS_S3_BUCKET:
        raise RuntimeError("S3 not configured. Set AWS_S3_BUCKET in environment.")
    key = f"curriculum/videos/w{session.week_number}/d{session.day_number}/{uuid.uuid4()}.mp4"
    s3 = _s3_client()
    s3.upload_fileobj(
        file, settings.AWS_S3_BUCKET, key,
        ExtraArgs={"ContentType": "video/mp4", "ServerSideEncryption": "AES256"},
    )
    return f"https://{settings.AWS_S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"


# Docx-embedded images only ever need to be one of these common web-safe raster types in
# practice; legacy vector formats (.wmf/.emf, from old copy-pasted Office art/charts) are a
# known, accepted limitation — mammoth will still hand them to the callback below and they'll
# upload fine, but they won't render as an <img> in a browser or React Native.
_IMAGE_EXT_BY_CONTENT_TYPE = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/gif": "gif",
    "image/bmp": "bmp",
    "image/tiff": "tiff",
}

_ALLOWED_HTML_TAGS = {
    "p", "h1", "h2", "h3", "h4", "h5", "h6",
    "strong", "em", "u", "s", "mark", "ul", "ol", "li", "img", "a", "blockquote", "br",
}
_ALLOWED_HTML_ATTRIBUTES = {
    "img": {"src", "alt"},
    "a": {"href"},
}


def upload_image_to_s3(file_bytes: bytes, content_type: str, session) -> str:
    """Uploads one docx-embedded image to S3, mirroring upload_video_to_s3's key/URL
    convention. `session` only needs .week_number/.day_number (a SimpleNamespace works,
    same pattern as upload_video_to_s3's caller in admin.py)."""
    if not settings.AWS_S3_BUCKET:
        raise RuntimeError("S3 not configured. Set AWS_S3_BUCKET in environment.")
    ext = _IMAGE_EXT_BY_CONTENT_TYPE.get(content_type, "png")
    key = f"curriculum/session_images/w{session.week_number}/d{session.day_number}/{uuid.uuid4()}.{ext}"
    s3 = _s3_client()
    s3.upload_fileobj(
        io.BytesIO(file_bytes), settings.AWS_S3_BUCKET, key,
        ExtraArgs={"ContentType": content_type, "ServerSideEncryption": "AES256"},
    )
    return f"https://{settings.AWS_S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"


def upload_pdf_to_s3(file, session) -> str:
    """Uploads an Additional Resources PDF, mirroring upload_video_to_s3's exact
    pattern. `session` only needs .week_number/.day_number."""
    if not settings.AWS_S3_BUCKET:
        raise RuntimeError("S3 not configured. Set AWS_S3_BUCKET in environment.")
    key = f"curriculum/additional_resources/w{session.week_number}/d{session.day_number}/{uuid.uuid4()}.pdf"
    s3 = _s3_client()
    s3.upload_fileobj(
        file, settings.AWS_S3_BUCKET, key,
        ExtraArgs={"ContentType": "application/pdf", "ServerSideEncryption": "AES256"},
    )
    return f"https://{settings.AWS_S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"


def convert_docx_to_html(docx_file, session) -> str:
    """Converts an uploaded .docx (file-like, opened in binary mode) to sanitized HTML,
    uploading each embedded image to S3 inline at its correct reading-order position via
    mammoth's image callback. `session` only needs .week_number/.day_number."""

    def _handle_image(image):
        with image.open() as image_bytes:
            data = image_bytes.read()
        url = upload_image_to_s3(data, image.content_type, session)
        attrs = {"src": url}
        alt_text = getattr(image, "alt_text", None)
        if alt_text:
            attrs["alt"] = alt_text
        return attrs

    result = mammoth.convert_to_html(
        docx_file,
        convert_image=mammoth.images.img_element(_handle_image),
        # Mammoth doesn't map highlighted text to any tag by default; "highlight" is a
        # recognized run-matcher in its style-map DSL even though it's undocumented in
        # the default map. Color fidelity (yellow vs green vs cyan, etc.) isn't preserved
        # here — every highlight color becomes a plain <mark>, which is a deliberate
        # simplification, not a bug.
        style_map="highlight => mark",
    )
    return nh3.clean(
        result.value,
        tags=_ALLOWED_HTML_TAGS,
        attributes=_ALLOWED_HTML_ATTRIBUTES,
        link_rel="noopener noreferrer",
    )
