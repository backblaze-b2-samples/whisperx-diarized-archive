<!-- last_verified: 2026-06-19 -->
# Architecture

`whisperx-diarized-archive` turns an audio/video library on Backblaze B2 into
a searchable, speaker-labeled transcript archive. Source media lands in B2
first; a local OSS pipeline (WhisperX → pyannote → sentence-transformers)
transcribes, diarizes, and embeds each file, writing transcripts, speaker
segments, and embeddings back to B2.

## Components

- **apps/web/** — Next.js 16 frontend (App Router, Tailwind v4, shadcn/ui)
  - Dashboard with archive metrics + recent transcriptions
  - Upload (audio/video → `media/` prefix) with drag-and-drop, progress
  - Library — media-only explorer with transcribe action, live progress, transcript viewer
  - Search — keyword + semantic search over the whole archive
  - Bucket Explorer (Files) — full-bucket browse with preview, download, delete
  - Dark mode via `next-themes`
- **services/api/** — FastAPI backend (layered architecture)
  - REST API for upload, listing, deletion, transcription, search
  - B2 S3 integration via boto3 (confined to `repo/`)
  - **Local ML engine** (`service/engine/`) — WhisperX transcription, pyannote diarization, sentence-transformers embeddings; heavy deps are lazy-imported and live in `requirements-ml.txt`
  - Health check endpoint with B2 connectivity verification
  - Structured JSON logging with request tracing
  - Prometheus-format metrics endpoint
- **packages/shared/** — TypeScript type definitions
  - Mirrors Pydantic models from the API
  - Consumed by `apps/web/` as workspace dependency

## Backend Layering

The API follows a strict layered architecture:

```
types/     Pydantic models — no logic, no imports from other layers
  |
config/    Settings (pydantic-settings) — depends only on types
  |
repo/      Data access (boto3 B2 client) — no business logic
  |
service/   Business logic — calls repo, returns types
  |
runtime/   FastAPI routes — calls service, never repo directly
```

### Layering Rules

1. Dependencies flow downward only: `types` -> `config` -> `repo` -> `service` -> `runtime`
2. No backward imports (e.g., service must not import from runtime)
3. `boto3` only allowed in `repo/` layer
4. All boundary data uses Pydantic models (no raw dicts across layers)
5. Each file stays under 300 lines

### Directory Structure

```
services/api/
  main.py                  App entrypoint, middleware, router registration
  app/
    types/                 Pydantic models (FileMetadata, Transcript, ArchiveItem, ...)
    config/                Settings loaded from environment (B2_REGION → endpoint)
    repo/                  B2 S3 client (b2_client.py) + artifact store (archive_store.py)
    service/               Business logic (upload, files, transcription, search, archive, jobs)
      engine/              Local ML compute — lazy-imported (transcribe / diarize / embed)
    runtime/               FastAPI route handlers (files, upload, archive, health, metrics)
  scripts/batch_transcribe.py   Bulk transcribe CLI
  requirements.txt         Base stack (FastAPI, boto3) — API boots with just this
  requirements-ml.txt      Heavy ML stack (whisperx, pyannote, torch, ...) — lazy
  tests/                   pytest tests (structural + integration)
```

## Boundary Invariants

- **No external SDK leakage**: `boto3` is only imported in `app/repo/`. All other layers interact with B2 through the repo interface.
- **ML inference is local compute, not storage**: the engine in `service/engine/` runs models on bytes the repo already fetched; it owns no boto3. Only boto3 is confined to `repo/`.
- **Lazy ML imports**: heavy ML libraries are imported inside engine functions, so the API boots and `pnpm test:api` / `pnpm check:structure` pass without `requirements-ml.txt` installed.
- **No raw dicts at boundaries**: All data crossing layer boundaries uses typed Pydantic models.
- **No mutable globals**: Configuration is read-only after init. The only module-level mutable state is the explicitly-ephemeral job registry (`service/jobs.py`), documented as process-local and non-authoritative.
- **Validated inputs**: All HTTP inputs validated by FastAPI/Pydantic. All object keys validated against path-traversal patterns.

## New repo methods (`repo/archive_store.py`)

- `get_object_bytes(key)` — download source media for processing
- `put_json(key, obj)` / `get_json(key)` — write/read transcript, segment, embedding artifacts
- `object_exists(key)` — authoritative "is this transcribed?" check
- `list_keys(prefix)` — bare key listing for batch + artifact iteration

## Deployment

- **Local dev** — `pnpm dev` runs both services via `concurrently`
  - Web: `localhost:3000`
  - API: `localhost:8000`
- **Railway** — two services from the same repo
  - See `infra/railway/README.md` for configuration

## Data Stores

- **Backblaze B2** — object storage (S3-compatible API), single bucket, sole data store (no DB)
  - B2 prefix layout:
    ```
    media/                 source audio/video (Upload writes here)
    transcripts/{key}.json word-aligned transcript + speaker labels
    segments/{key}.json    speaker segments (text, speaker, start, end)
    embeddings/{key}.json  per-segment embedding vectors + segment refs
    ```
  - Listing/metadata via S3 `list_objects_v2` / `head_object`; artifacts via `get_object` / `put_object`
  - Library + dashboard status is **derived** from listings (transcript exists ⇒ transcribed)
  - Semantic search loads `embeddings/*` and ranks in-process (small-archive caveat; a vector DB is the scale path)

## External Services

- **Backblaze B2 S3 API** — storage, retrieval, deletion, presigned URLs
- **HuggingFace Hub** — download-only, used once to fetch pyannote's gated diarization weights with a **free** `HF_TOKEN`. Not an inference API; no per-call cost. Optional — diarization degrades to transcribe-only when unset.
- No remote inference API: WhisperX, pyannote, and sentence-transformers all run **locally**.

## Trust Boundaries

See [docs/SECURITY.md](docs/SECURITY.md) for full security documentation.

- **Frontend -> API** — CORS-restricted to configured origins
- **API -> B2** — authenticated via application keys, signature v4
- **Client -> B2** — presigned URLs for download (10-min expiry, forced attachment)

## Data Flows

- **Upload**: Browser -> `POST /upload` (multipart) -> API validates -> repo writes to B2 `media/` -> response
- **Transcribe**: Browser -> `POST /archive/transcribe {key}` -> enqueue background job -> `transcription` service: repo `get_object_bytes` -> engine `transcribe` (WhisperX, word-aligned) -> engine `diarize` (pyannote, if `HF_TOKEN`) -> engine `embed` (sentence-transformers) -> repo `put_json` x3 (`transcripts/`, `segments/`, `embeddings/`)
- **Library/status**: Browser -> `GET /archive/items` -> service lists `media/` + reads matching `transcripts/*` -> derived status
- **Search**: Browser -> `GET /archive/search` -> keyword (substring over `segments/*`) or semantic (cosine over `embeddings/*`, query embedded by the engine)
- **List/Download/Delete (Files)**: same as the starter — `GET /files`, `GET /files/{key}/download`, `DELETE /files/{key}`

## Observability

- Structured JSON logging on all requests with `request_id`
- Request timing middleware (logs duration per request)
- `/metrics` endpoint (Prometheus format: request count, latency, upload count)
- `/health` endpoint (B2 connectivity check)

## Canonical Files

- Layered API handler: `services/api/app/runtime/archive.py`
- Pipeline orchestration: `services/api/app/service/transcription.py`
- Local ML engine (lazy): `services/api/app/service/engine/`
- B2 data access (repo layer): `services/api/app/repo/b2_client.py`, `services/api/app/repo/archive_store.py`
- Pydantic models: `services/api/app/types/` (`archive.py`, `files.py`, `upload.py`, `stats.py`, `formatting.py`)
- Config (pydantic-settings, region→endpoint): `services/api/app/config/settings.py`
- Structural tests: `services/api/tests/test_structure.py`
- Frontend API client: `apps/web/src/lib/api-client.ts`
- Shared TypeScript types: `packages/shared/src/types.ts`

## Core Features

- [Media Upload](docs/features/file-upload.md)
- [Transcription & Diarization](docs/features/transcription.md)
- [Search](docs/features/search.md)
- [Archive Library](docs/features/archive-library.md)
- [Bucket Explorer (Files)](docs/features/file-browser.md)
- [Dashboard](docs/features/dashboard.md)

## References

- [docs/SECURITY.md](docs/SECURITY.md) — security principles and implementation
- [docs/RELIABILITY.md](docs/RELIABILITY.md) — reliability expectations
- [AGENTS.md](AGENTS.md) — architectural invariants and agent instructions
