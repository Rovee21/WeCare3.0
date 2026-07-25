# WECARE 3.0

A bilingual (English + Mandarin) mobile app delivering a structured 7-week caregiving curriculum to Chinese-American family caregivers. Built with React Native (frontend) and Django REST Framework (backend).

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Prerequisites](#prerequisites)
3. [Running the Mobile App](#running-the-mobile-app)
4. [Running the Backend](#running-the-backend)
5. [Environment Variables](#environment-variables)
6. [Key Commands](#key-commands)
7. [E2E Testing](#e2e-testing)
8. [API Contract & Codegen](#api-contract--codegen)
9. [Pre-commit Hooks](#pre-commit-hooks)
10. [Tech Stack](#tech-stack)
11. [App Overview](#app-overview)

---

## Project Structure

```
WeCare3.0/
  mobile/                       # React Native + Expo user-facing app
    App.js                      # Entry point
    app.json                    # Expo config
    babel.config.js
    package.json
    src/
      screens/                  # One file per screen
      navigation/               # RootNavigator (stack + bottom tabs)
      services/                 # All API calls (authService, sessionService, userService, journalService)
      api/                      # Hand-written typed client (client.ts) — wraps openapi-fetch
      generated/                # Generated code only (schema.d.ts) — do not hand-edit, see scripts/generate-api.sh
      i18n/                     # Translations (en.json, zh.json)
      constants/                # Colors, theme
  backend/                      # Django REST API + Admin Console
    manage.py
    docker-compose.yml          # Runs Postgres + Django together
    Dockerfile
    requirements.txt
    generated/                  # Generated code only (openapi-schema.yaml) — regenerate with scripts/generate-api.sh
    .env.example                # Copy this to .env and fill in values
    participants/               # Enrollment, auth, participant model
    content/                    # Sessions, engagement logs, notifications
    journal/                    # Voice journal entries
    wecare/
      settings/
        base.py                 # Shared settings
        local.py                # Local dev overrides
        production.py           # Production overrides
  scripts/
    generate-api.sh             # Regenerates backend/generated/openapi-schema.yaml + mobile/src/generated/schema.d.ts (Dockerized, no host installs)
```

---

## Prerequisites

Make sure you have these installed before starting:

- **Node.js** 18+ — `node --version`
- **Expo Go** app on your phone (iOS or Android) — download from the App Store / Play Store
- **Docker Desktop** — required to run the backend locally
- **Python 3.11+** — only needed if you want to run Django outside Docker

---

## Running the Mobile App

The mobile app now connects to the real backend (no more mock auth/data). The backend must be running first — see [Running the Backend](#running-the-backend).

**Step 1 — Install dependencies**

```bash
cd mobile
npm install
```

**Step 2 — Set your backend URL**

Open `mobile/src/services/api.js` and set `BASE_URL` to your machine's local IP (not `localhost` — a physical phone can't reach your laptop's localhost):

```js
export const BASE_URL = __DEV__ ? 'http://YOUR_LOCAL_IP:8000/api' : 'https://your-production-domain.com/api';
```

Find your IP with `ipconfig` (Windows) or `ipconfig getifaddr en0` (Mac). This changes whenever you reconnect to Wi-Fi, so re-check it if requests start failing.

**Step 3 — Start the dev server**
```bash
npx expo start --clear
```

**Step 4 — Open on your phone**

Scan the QR code with the Expo Go app. Phone and computer must be on the same Wi-Fi network.

**What you should see:**
- Enrollment screen on first launch (no token stored yet)
- Enter a real enrollment code generated from Django Admin → real token issued and stored in SecureStore
- Bottom tab bar: Home | Courses | Journal | Settings
- Tapping into a course session plays real video (if `video_url` is set) and logs engagement to the backend
- Journal tab opens the Voice Journal recorder → record → confirm → emotion/stress survey → uploads to backend

**Windows only — firewall:** if the phone can't reach the backend, allow port 8000 (this does not persist across reboots, re-run after restarting):
```powershell
New-NetFirewallRule -DisplayName "Allow Port 8000" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
```

---

## Running the Backend

The backend uses Docker Compose, which starts both Postgres and Django with a single command. You do not need to install Python or Postgres separately.

**Step 1 — Copy the environment file**
```bash
cd backend
cp .env.example .env
```

Open `.env` and set `SECRET_KEY` to any long random string for local dev. Leave AWS fields blank — they are only needed for S3 and Transcribe.

**Step 2 — Start the services**
```bash
docker-compose up
```

This starts:
- `db` — Postgres on port 5432
- `web` — Django on port 8000

On first run, Docker builds the image and pulls Postgres. Subsequent starts are fast.

**Step 3 — Run migrations** (first time only, in a separate terminal)
```bash
docker-compose exec web python manage.py migrate
```

**Step 4 — Create an admin account** (first time only)
```bash
docker-compose exec web python manage.py createsuperuser
```

**Step 5 — Open Django Admin**

Go to `http://localhost:8000/admin` and log in with the superuser credentials you just created.

From Django Admin you can:
- Add participants (name, email, language, cohort assignment)
- Generate enrollment codes
- Add curriculum sessions (content for each week/day)
- View engagement logs and notification records

**Step 6 — Test the enrollment API**

```bash
curl -X POST http://localhost:8000/api/enroll/ \
  -H "Content-Type: application/json" \
  -d '{"code": "YOUR_CODE_HERE"}'
```

A successful response returns a token, language, participant ID, and cohort data.

**Resetting a participant for repeat testing**

Enrollment codes are single-use. To re-test the full enrollment flow without going through Django Admin each time:
```bash
docker-compose exec web python manage.py reset_participant
```
This resets the first participant (clears `is_enrolled`, deletes their old token) and prints a fresh enrollment code.

**Local media files (video/audio for course sessions)**

For local dev, video and audio files can be served directly from Django instead of S3. Drop files into `backend/media/session_videos/` or `backend/media/session_audio/`, then set the session's `video_url` / `audio_url` field (in Django Admin or via shell) to:
```
http://YOUR_LOCAL_IP:8000/media/session_videos/your_file.mp4
```
Use your local IP, not `localhost`, so the phone can reach it. This only works locally — production uses S3 + CloudFront.

---

## Environment Variables

### Mobile app

Copy `mobile/.env.example` to `mobile/.env` to override the API base URL (`EXPO_PUBLIC_API_URL`). It defaults to `http://localhost:8000`, which works for the iOS Simulator against `docker-compose up` in `backend/`. Physical devices need your machine's LAN IP; the Android emulator needs `http://10.0.2.2:8000`. See `mobile/src/services/api.js`.

### Backend (`backend/.env`)

Copy from `backend/.env.example`. Required fields:

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key — any long random string for local dev |
| `DEBUG` | `True` for local dev, `False` in production |
| `DATABASE_URL` | Postgres connection string — pre-filled for Docker |
| `ALLOWED_HOSTS` | `*` for local dev |
| `CORS_ALLOW_ALL_ORIGINS` | `True` for local dev |
| `AWS_ACCESS_KEY_ID` | Leave blank for local dev |
| `AWS_SECRET_ACCESS_KEY` | Leave blank for local dev |
| `AWS_S3_BUCKET` | S3 bucket name for curriculum media |
| `AWS_TRANSCRIBE_OUTPUT_BUCKET` | S3 bucket for VJ transcripts |
| `EMAIL_HOST_PASSWORD` | Gmail app password for sending enrollment codes |


---

## Key Commands

### Mobile (run from the `mobile/` directory)
```bash
cd mobile
npm install              # Install dependencies
npx expo start --clear   # Start dev server (clears cache)
npx expo start --ios     # iOS simulator only
npx expo start --android # Android emulator only
npm run generate:api     # Regenerate src/generated/schema.d.ts from backend/generated/openapi-schema.yaml
```

### Backend (run from the `backend/` directory)
```bash
cd backend
docker-compose up                                          # Start everything
docker-compose up -d                                       # Start in background
docker-compose down                                        # Stop everything
docker-compose exec web python manage.py migrate           # Run migrations
docker-compose exec web python manage.py makemigrations    # Create new migrations
docker-compose exec web python manage.py createsuperuser   # Create admin account
docker-compose exec web python manage.py shell             # Django shell
docker-compose logs web                                    # View Django logs
```

---

## E2E Testing

`e2e/run.sh` drives the real app (iOS Simulator, via Expo Go) against the real Dockerized backend using [Maestro](https://maestro.mobile.dev). No mocking — it exercises actual network calls, the actual database, and actual audio recording.

**One-time setup:**
```bash
brew tap mobile-dev-inc/tap
brew install mobile-dev-inc/tap/maestro
```
(Plain `brew install maestro` installs an unrelated app of the same name — use the tap above.)

Maestro runs on the JVM, so it needs a Java runtime on the host. Most Macs don't have one by default — if `maestro --version` fails with something like `Unable to locate a Java Runtime`, install one:
```bash
brew install openjdk
```
(Follow the symlink instructions `brew` prints after install, so `java` is on your `PATH`.)

The iOS Simulator also needs microphone access for the voice-journal flow: macOS System Settings → Privacy & Security → Microphone → enable **Simulator**. This is a one-time host-level grant that can't be scripted.

**Running:**
```bash
open -a Simulator                # boot a simulator first if none is running
npm run e2e:ios --prefix mobile  # or: e2e/run.sh
```

The script starts `backend/docker-compose`, waits for it to respond, resets the test participant (`reset_participant`) to get a fresh single-use enrollment code, deep-links Expo Go to whatever Metro dev server is running (reusing one you already have open, or starting one), and runs every flow in `e2e/flows/`. Each flow gets its own fresh reset + code, since enrollment codes are single-use and the app has no "already enrolled" bootstrap check (it always starts at the Enrollment screen).

Flows are plain Maestro YAML (`e2e/flows/*.yaml`), targeting `testID`s added to the relevant screens. Add new flows by dropping another `.yaml` file in that directory.

---

## API Contract & Codegen

The backend's API is documented as an OpenAPI 3 schema via [drf-spectacular](https://drf-spectacular.readthedocs.io/), and the mobile app's API client is generated from that schema instead of being hand-written — this is the source of truth for what the backend actually returns, so the two sides can't drift out of sync.

- **Browse the API interactively:** `http://localhost:8000/api/schema/swagger-ui/` (backend must be running)
- **Raw schema:** `http://localhost:8000/api/schema/`, or the checked-in `backend/generated/openapi-schema.yaml`
- **Generated mobile types:** `mobile/src/generated/schema.d.ts` (do not hand-edit — regenerate it)
- **Typed client:** `mobile/src/api/client.ts` (hand-written, not generated) wraps [openapi-fetch](https://openapi-ts.dev/openapi-fetch/) with auth-token injection (mirrors the old `apiFetch` behavior) and an `unwrap()` helper that throws on error responses, so service functions keep their original signatures.

**Regenerating after a backend API change:**
```bash
./scripts/generate-api.sh
```
This runs entirely in Docker (a `manage.py spectacular` call inside the `web` container, plus a `node:20-alpine` container for `openapi-typescript`) — nothing is installed on the host. Requires the backend containers to be running (`docker-compose up -d` from `backend/`).

**Design notes:**
- The wire format is **snake_case** end-to-end (matches Django/DRF convention) — the mobile services no longer do manual `snake_case → camelCase` remapping.
- Function-based `@api_view` views (all of them, in this codebase) don't get automatic schema inference from drf-spectacular the way class-based generic views/viewsets do — every view has an explicit `@extend_schema(request=..., responses=...)` annotation. Keep this in mind when adding a new endpoint: without the annotation, it'll show up in the schema with an empty body.
- One deliberate exception: `journalService.directUpload()` (multipart audio upload) bypasses the typed client and calls `fetch` directly. OpenAPI has no distinct binary-file type for multipart fields, so drf-spectacular represents Django's `FileField` as a `string`, which isn't usable for an actual file upload — forcing it through the typed client would fight the type system for no benefit.

---

## Pre-commit Hooks

This repo uses [pre-commit](https://pre-commit.com) to run repo-local checks before each commit. Right now there's one hook, `api-codegen-freshness` (see `.pre-commit-config.yaml`): whenever a commit touches backend Python code or the generated API files, it re-runs `scripts/generate-api.sh` and blocks the commit if that produces a diff — this is what actually enforces the [API Contract & Codegen](#api-contract--codegen) rule that `backend/generated/openapi-schema.yaml` and `mobile/src/generated/schema.d.ts` stay in sync with the backend code.

**One-time setup (Mac):**
```bash
brew install pre-commit
```
Then, from the repo root, install the git hook so it actually runs on `git commit`:
```bash
pre-commit install
```

The `api-codegen-freshness` hook shells out to `scripts/generate-api.sh`, which runs against the backend Docker containers — start those first (`cd backend && docker-compose up -d`) or commits touching backend/generated code will fail with a "container isn't running" error rather than a real codegen diff.

To run all hooks on demand without committing (e.g. to check before pushing):
```bash
pre-commit run --all-files
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Mobile | React Native, Expo SDK 54, Expo Go for dev |
| Navigation | React Navigation v7 (stack + bottom tabs) |
| Internationalization | react-i18next (English + Mandarin) |
| Audio recording | `expo-audio` (Voice Journal) |
| Video playback | `expo-video` (course session video tab) |
| API client | Types generated from OpenAPI via `openapi-typescript` (`src/generated/`) + hand-written `openapi-fetch` client (`src/api/`); TypeScript for those plus `src/services/`, rest of the app stays JS |
| Backend | Django 4.2, Django REST Framework |
| API schema | `drf-spectacular` (OpenAPI 3) |
| Database | PostgreSQL (local via Docker, production via AWS RDS) |
| Auth | DRF token auth (one-time enrollment code → permanent token) |
| Storage | AWS S3 (curriculum media, VJ audio recordings) |
| Transcription | AWS Transcribe (async, server-side) |
| Push Notifications | Firebase Cloud Messaging + AWS SNS |
| Admin Console | Django Admin |

---

## App Overview

### Cohort System (3 layers)

Every participant is assigned three cohort dimensions at enrollment from their baseline survey:

| Layer | Field | Values |
|---|---|---|
| 1 | `group1` | `intervention` / `non_intervention` |
| 2 | `group2` | `mild` / `moderate` / `severe` (care recipient functional status) |
| 3 | `group3` | `high` / `low` (baseline stress level, updated by weekly VJ) |

These three values drive all content routing.

### Auth Flow

1. Research team enters participant data into Django Admin and generates a one-time enrollment code
2. Code is emailed to the participant
3. Participant enters code in the app → backend validates → returns token + language + cohort profile
4. Token is stored permanently in device SecureStore — no re-login ever

### Screens

| Screen | Purpose |
|---|---|
| Enrollment | One-time code entry; language auto-set from backend response |
| Home | Today's session card + Go to Courses + Voice Journal |
| Courses | Full session list grouped by week; search by title |
| Daily Session | Video / Audio / Text tabs (real video playback via `expo-video`), resources, emoji feedback, engagement tracking (time spent, video opens) |
| Voice Journal | Audio recording (`expo-audio`) → confirm → emotion (7 options) + stress level (1–10) survey → uploads to backend |
| Settings | Contact us, delete account |

### Voice Journal Integration

The Voice Journal was originally a standalone app — it is now merged directly into WECARE as a tab, not a separate app. Recordings upload via `POST /api/journal/direct-upload/` (multipart). Locally, audio is saved to `MEDIA_ROOT`; in production (once AWS credentials are set), the same endpoint will upload to S3 and trigger AWS Transcribe automatically — no frontend changes required for that upgrade.

### Engagement Tracking

`DailySessionScreen` logs engagement automatically:
- Time spent on a session (via screen mount/unmount timer)
- Video open count
- Emoji reactions
- Read/unread state (`mark_read`)

All of this is visible per-participant in Django Admin under each participant's detail page (Engagement Log, Session Completions, Voice Journal Submissions sections).

### Django Admin (Research Team)

- Add/edit participants with full cohort assignment
- Generate and email enrollment codes
- Upload curriculum sessions (week, day, content URLs)
- View engagement logs, notification sending records

### Push Notifications

- Daily at 12pm: session reminder
- 24hr unread reminder: if participant hasn't opened today's session
- Weekly VJ reminder: on scheduled journal weeks
