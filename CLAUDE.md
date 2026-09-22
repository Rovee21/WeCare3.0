# WeCare 3.0

Django REST backend (`backend/`) + Expo/React Native mobile app (`mobile/`) for a
caregiver-support research study (video/text sessions, voice journaling, engagement
tracking, participant admin).

## Backend apps
- `content/` — Sessions (video/text/docx-derived rich text), engagement logging,
  completion tracking, notifications.
- `journal/` — Voice Journal (VJ): prompts, audio recording entries, transcription.
- `participants/` — Participant records, cohort/enrollment, CSV import, custom admin
  dashboards (stats, recordings).

## S3 usage — manual boto3, no django-storages
There is no `django-storages`/`DEFAULT_FILE_STORAGE` wiring. Every S3 upload is a
direct `boto3` call in a small `services.py` per app (`content/services.py`,
`journal/services.py`), each with a private `_s3_client()` builder (small, deliberately
duplicated rather than shared across apps) and a key convention like
`{prefix}/w{week}/d{day}/{uuid4}.{ext}`.

**Buckets are split by sensitivity, not just by app:**
- `wecare-content` (`AWS_S3_BUCKET`) — curriculum videos/images. Public read via bucket
  policy, scoped per key-prefix (e.g. `curriculum/videos/*`, `curriculum/session_images/*`)
  — a new prefix needs an explicit bucket-policy addition or it 403s even after a
  successful upload.
- `wecare-vj-audio` (`AWS_S3_VJ_AUDIO_BUCKET`) — Voice Journal recordings (participant
  health-related audio). Stays fully private; every read goes through a short-lived
  presigned `get_object` URL (`journal/services.py`'s `generate_audio_download_url`),
  never a public link.

When adding a new kind of upload, decide up front which category it belongs to instead
of defaulting to the public bucket.

## Django admin — custom dashboard pattern
Several admin pages beyond the standard changelist are custom views following the same
recipe (see `participants/admin.py`'s `stats_view`, `csv_import_view`,
`recordings_view`, and `content/admin.py`'s docx-upload form fields):
- Extra routes added via `get_urls()` returning `custom_paths + super().get_urls()`,
  wrapped in `self.admin_site.admin_view(...)`.
- A button linking to the custom view is injected into the changelist via
  `changelist_view()`'s `extra_context`, rendered in a
  `templates/admin/<app>/<model>/change_list.html` override's `object-tools-items`
  block.
- The view itself renders a `TemplateResponse` with `**self.admin_site.each_context(request)`
  merged in, using the same dark-header `.stats-table` CSS already established in
  `templates/admin/participant_stats.html` — reuse that styling rather than inventing
  new CSS per dashboard.
- A virtual (non-model) upload `FileField` on a `ModelForm`, validated in
  `clean_<field>()` and converted/injected into a real model field in `clean()` — see
  `content/admin.py`'s `SessionAdminForm` (`video_upload` → `video_url`, `docx_upload`
  → `text_content_html`) — is the established pattern for "upload X, derive Y" admin
  fields.

## API contract — codegen must stay in sync
`mobile/src/generated/schema.d.ts` is generated from `backend/generated/openapi-schema.yaml`.
After changing any serializer/view/URL, rebuild the backend and run
`MSYS_NO_PATHCONV=1 ./scripts/generate-api.sh` from the repo root, then stage both
generated files together — `scripts/check-api-codegen.sh` fails CI on a stale regen.

## Local dev
`cd backend && docker-compose up -d --build`. The `web` service bind-mounts the repo
(`.:/app`) so Python/template edits take effect via Django's autoreloader without a
rebuild — `--build` is only needed after a `requirements.txt` change. AWS-dependent
features (S3 uploads, docx conversion, VJ recordings) need real credentials in
`backend/.env`, loaded via `env_file:` in `docker-compose.yml`.

## Handling `.env` and AWS credentials
Do not read, write, or edit any `.env`/`.env.*` file directly — tell the user what
key/value to set and let them edit it themselves. Do not run AWS CLI or boto3 calls
against the user's real AWS account (directly, or indirectly via `docker exec`/`docker
compose exec` against a container with credentials loaded) unless the user explicitly
asks for that specific action in that moment — they manage AWS console/CLI actions
(bucket creation, policy changes, IAM) themselves.
