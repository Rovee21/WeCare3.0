import io
import re
import uuid
from pathlib import Path
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


def _delete_s3_object_by_url(url: str) -> None:
    """Best-effort delete of the S3 object referenced by a full public URL previously
    returned by upload_media_asset_to_s3 (https://{bucket}.s3.{region}.amazonaws.com/{key}).
    Used when a Media Library asset is replaced, so the old file doesn't linger as an
    orphaned, unreferenced object. Never raises — a cleanup failure shouldn't block the
    replace itself, since the new file is already uploaded and the database already
    points at it by the time this runs."""
    if not url or not settings.AWS_S3_BUCKET:
        return
    prefix = f"https://{settings.AWS_S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/"
    if not url.startswith(prefix):
        return
    key = url[len(prefix):]
    try:
        _s3_client().delete_object(Bucket=settings.AWS_S3_BUCKET, Key=key)
    except Exception:
        pass


_IMG_SRC_RE = re.compile(r'<img[^>]+src="([^"]+)"')


def extract_image_urls(html_content: str) -> list:
    """Pulls every <img src="..."> URL out of a MediaAsset's html_content (Document
    assets only) — html_content is never hand-edited by an admin (unlike a Session's own
    text_content_html, which is), so this reliably reflects exactly the set of images
    that particular conversion uploaded, letting cleanup code find them again without a
    separate tracking field/migration."""
    return _IMG_SRC_RE.findall(html_content or "")


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
    """Uploads one docx-embedded image to S3 under a per-session week/day key.
    `session` only needs .week_number/.day_number (a SimpleNamespace works, same
    pattern as convert_docx_to_html's caller in admin.py)."""
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


def upload_media_library_document_image_to_s3(file_bytes: bytes, content_type: str) -> str:
    """Uploads one image embedded in a Media Library Word document, mirroring
    upload_image_to_s3's shape but flat-keyed (library documents aren't tied to any one
    session's week/day)."""
    if not settings.AWS_S3_BUCKET:
        raise RuntimeError("S3 not configured. Set AWS_S3_BUCKET in environment.")
    ext = _IMAGE_EXT_BY_CONTENT_TYPE.get(content_type, "png")
    key = f"curriculum/media_library/document_images/{uuid.uuid4()}.{ext}"
    s3 = _s3_client()
    s3.upload_fileobj(
        io.BytesIO(file_bytes), settings.AWS_S3_BUCKET, key,
        ExtraArgs={"ContentType": content_type, "ServerSideEncryption": "AES256"},
    )
    return f"https://{settings.AWS_S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"


# Default ext/content-type per asset_type, used when a caller doesn't know the actual
# uploaded file's own extension (e.g. SessionAdminForm's video/PDF uploads, which are
# always exactly one format). Types that accept more than one real-world extension
# (Audio: mp3/m4a, Image: jpg/png) should have callers pass the real ext/content_type
# instead of relying on these defaults.
_MEDIA_ASSET_DEFAULT_EXT_CONTENT_TYPE = {
    "Video": ("mp4", "video/mp4"),
    "PDF": ("pdf", "application/pdf"),
    "Audio": ("mp3", "audio/mpeg"),
    "Document": ("docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    "Image": ("jpg", "image/jpeg"),
}

# Content-type fallback by extension, used by build_media_asset_fields when the
# uploaded file's own content_type is missing/unreliable.
_CONTENT_TYPE_BY_EXT = {
    ".mp4": "video/mp4",
    ".pdf": "application/pdf",
    ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}


def upload_media_asset_to_s3(file, asset_type: str, ext: str = None, content_type: str = None) -> str:
    """Uploads a Media Library asset (video/PDF/audio/document/image) — the single
    upload path for Session video/text-PDF and Additional Resource PDF fields, all of
    which point at a MediaAsset row via FK rather than each managing their own S3
    upload. Assets are reusable across sessions, so this uses its own flat key prefix
    rather than a per-session week/day one. Nested under curriculum/ so it's already
    covered by the existing public-read bucket policy on that prefix.

    `ext`/`content_type` default to the asset_type's single expected format (e.g. always
    .mp4 for Video) — pass them explicitly for types that accept more than one real
    extension (Audio, Image), so the S3 key/Content-Type match what was actually
    uploaded."""
    if not settings.AWS_S3_BUCKET:
        raise RuntimeError("S3 not configured. Set AWS_S3_BUCKET in environment.")
    default_ext, default_content_type = _MEDIA_ASSET_DEFAULT_EXT_CONTENT_TYPE[asset_type]
    ext = (ext or default_ext).lstrip(".")
    content_type = content_type or default_content_type
    key = f"curriculum/media_library/{asset_type.lower()}/{uuid.uuid4()}.{ext}"
    s3 = _s3_client()
    s3.upload_fileobj(
        file, settings.AWS_S3_BUCKET, key,
        ExtraArgs={"ContentType": content_type, "ServerSideEncryption": "AES256"},
    )
    return f"https://{settings.AWS_S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"


def convert_docx_to_html(docx_file, upload_image_fn) -> str:
    """Converts an uploaded .docx (file-like, opened in binary mode) to sanitized HTML,
    uploading each embedded image to S3 inline at its correct reading-order position via
    mammoth's image callback. `upload_image_fn(data: bytes, content_type: str) -> str`
    lets callers choose the image key convention — a per-session week/day one (see
    admin.py's SessionAdminForm) or the flat Media Library one
    (upload_media_library_document_image_to_s3)."""

    def _handle_image(image):
        with image.open() as image_bytes:
            data = image_bytes.read()
        url = upload_image_fn(data, image.content_type)
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


def build_media_asset_fields(file, asset_type: str) -> dict:
    """Uploads `file` (and, for Document assets, also converts it to HTML) and returns
    the field values MediaAsset.objects.create(...) needs — shared by the single-asset
    admin form and the bulk-upload view so both create assets identically.

    Reads the upload into memory once and hands each downstream consumer (S3 upload,
    docx conversion) its own independent BytesIO, rather than reusing `file` itself for
    both — boto3's S3 upload can close/exhaust the underlying stream on a real-sized
    file (multipart transfers manage the stream's lifecycle themselves), which broke a
    second read from the same object with "I/O operation on closed file" for Document
    assets in practice.

    Derives the S3 key's extension and Content-Type from the upload's own filename/
    content_type rather than a fixed per-asset_type default, since Audio (mp3/m4a) and
    Image (jpg/png) each accept more than one real extension."""
    ext = Path(file.name).suffix.lower()
    content_type = getattr(file, "content_type", None) or _CONTENT_TYPE_BY_EXT.get(ext)
    raw = file.read()
    fields = {
        "file_url": upload_media_asset_to_s3(io.BytesIO(raw), asset_type, ext=ext, content_type=content_type),
        "original_filename": file.name,
    }
    if asset_type == "Document":
        fields["html_content"] = convert_docx_to_html(io.BytesIO(raw), upload_media_library_document_image_to_s3)
    return fields


def create_or_replace_media_asset(title: str, asset_type: str, file, replace_existing: bool):
    """Creates a new MediaAsset, or — if one with the same (title, asset_type) already
    exists — either replaces it in place or skips the upload entirely, depending on
    `replace_existing`. "Replace in place" means updating the existing row's
    file/html_content/original_filename rather than creating a second row, so its id
    (and any Session/AdditionalResource FK already pointing at it) is unaffected —
    picking up the new content automatically, no re-pick needed. The old file's S3
    object is deleted once the new one is safely uploaded and saved, so a replace
    doesn't leak an orphaned copy in the bucket — for a Document asset, that includes
    every image embedded in its *previous* html_content too, since re-converting the
    new .docx uploads a fresh set of embedded images under new keys regardless.

    Returns (asset, status), where status is one of "created", "replaced",
    "skipped_duplicate" (asset is None in the skipped case)."""
    from .models import MediaAsset

    existing = MediaAsset.objects.filter(title=title, asset_type=asset_type).first()
    if existing and not replace_existing:
        return None, "skipped_duplicate"

    fields = build_media_asset_fields(file, asset_type)
    if existing:
        old_file_url = existing.file_url
        old_image_urls = extract_image_urls(existing.html_content) if existing.asset_type == MediaAsset.TYPE_DOCUMENT else []
        for key, value in fields.items():
            setattr(existing, key, value)
        existing.save()
        if old_file_url and old_file_url != existing.file_url:
            _delete_s3_object_by_url(old_file_url)
        for img_url in old_image_urls:
            _delete_s3_object_by_url(img_url)
        return existing, "replaced"

    asset = MediaAsset.objects.create(title=title, asset_type=asset_type, **fields)
    return asset, "created"
