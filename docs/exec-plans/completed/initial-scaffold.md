# Scaffold plan — `whisperx-diarized-archive`

Source of truth: `.claude/scratch/vcsk-3b9d80cc-a4c5-432f-9cf4-ab401a454437/`
(fresh vibe-coding-starter-kit clone). Build target: `./whisperx-diarized-archive`.

---

## 1. Purpose

`whisperx-diarized-archive` is a B2 sample for **podcast producers, compliance
teams, and content researchers** who drop an audio/video library into Backblaze
B2 and turn it into a **searchable, speaker-labeled transcript archive**. Source
media lands in B2 first; a local OSS pipeline then transcribes each file with
**WhisperX** (word-aligned), assigns speaker labels with **pyannote**, embeds
each speaker segment with **sentence-transformers**, and writes transcripts,
speaker-segment files, and an embedding index back to B2. A web UI lets users
browse the media library, watch transcription progress, read speaker-attributed
transcripts, and **search the whole archive by keyword or semantic similarity**.
The story B2 tells here is **sustained write-amplification**: one uploaded media
file fans out into dense, continuously-accumulating transcript / segment /
embedding artifacts across a growing archive — all on B2 via the S3 API with a
custom user-agent and standard `B2_*` env vars. Everything runs on local OSS;
the only credential beyond B2 is a **free** HuggingFace token used solely to
download pyannote's gated diarization weights.

## 2. Architecture delta from vibe-coding-starter-kit

The starter kit is the ceiling: a Next.js 16 + FastAPI (layered) monorepo with a
UI kit, Upload, File Explorer, Dashboard, and a clean `types->config->repo->service->
runtime` backend. We **keep the scaffold**, **trim image/PDF specifics**, and
**add the transcription/diarization/embedding pipeline + library + search**.

### KEEP (as-is or near-verbatim)
- Entire monorepo shape: `apps/web`, `services/api`, `packages/shared`, `infra/railway`, `scripts/`.
- UI kit / design system: `apps/web/src/components/ui/`, `globals.css` tokens, `/design` page. **(starter contract — never edit generated `ui/`)**
- **Bucket Explorer** — `/files` route + `apps/web/src/app/files/` + `components/files/` + its sidebar entry. **NON-NEGOTIABLE KEEP** (full-bucket browse).
- **Upload** — `/upload` route + `components/upload/` + sidebar entry. Now the on-ramp for source media (MP3/WAV/MP4...), writing to the `media/` prefix.
- `/settings` page, layout/sidebar shell, error/empty-state patterns, TanStack Query data layer (`lib/queries.ts`, `lib/api-client.ts`).
- Backend layering + structural tests (`tests/test_structure.py`), `/health`, `/metrics`, JSON logging, CORS, doctor preflight, single-root `.env`.
- B2 repo adapter `repo/b2_client.py` (boto3-only-in-repo invariant) — extended, not replaced.

### TRIM (remove from starter)
- **Image/PDF metadata extraction** — `services/api/app/service/metadata.py`, its call site in the upload service, and deps `Pillow` + `PyPDF2` (image EXIF / PDF page-count are irrelevant to audio/video). Delete `docs/features/metadata-extraction.md`. Keep `python-magic` ONLY if it is wired into upload content-type validation; otherwise drop it and fall back to `mimetypes`. Drop any metadata-extraction structural/unit tests.
- Starter "this is a template / Use this template" framing in README/AGENTS (this is now a finished sample app, not a template). Keep the layering invariants and the keep/adapt contract language where still useful.

### ADD (new for whisperx-diarized-archive)
Backend (`services/api/app/`):
- `repo/b2_client.py` additions: `get_object_bytes(key)` (download media for processing), `put_json(key, obj)` / `get_json(key)` (transcript/segment/embedding artifacts), `list_keys(prefix)` helper. boto3 stays confined here.
- `service/transcription.py` — orchestrates one media file: pull bytes from B2 -> run engine -> write `transcripts/`, `segments/`, `embeddings/` artifacts back to B2. No boto3 (calls repo).
- `service/engine/` — the local ML engine, **lazy-imported** so the API boots without the heavy stack:
  - `transcribe.py` (WhisperX / faster-whisper, word-aligned),
  - `diarize.py` (pyannote `speaker-diarization-3.1`; assigns speakers to words/segments; **graceful-degrade**: if `HF_TOKEN` unset -> transcribe-only + clear warning),
  - `embed.py` (sentence-transformers `all-MiniLM-L6-v2`, one vector per speaker segment).
- `service/search.py` — keyword (substring over segment text) and semantic (cosine over segment embeddings) search across the archive; returns segments with speaker + start/end + source key.
- `service/jobs.py` — process-local job registry tracking live progress (queued->transcribing->diarizing->embedding->writing->done/error). Documented as ephemeral; the **authoritative** "is this file transcribed?" signal is the existence of its `transcripts/{key}.json` in B2.
- `service/stats.py` (or extend existing stats) — archive metrics for the dashboard.
- `types/` additions: `Segment`, `Transcript`, `SpeakerSegment`, `SearchHit`, `TranscriptionJob`, `ArchiveItem`, `ArchiveStats` Pydantic models.
- `runtime/archive.py` — new router:
  - `POST /archive/transcribe` `{key}` -> enqueue background job, return job id
  - `GET /archive/jobs` and `GET /archive/jobs/{id}` -> job status/progress
  - `GET /archive/items` -> media list + transcription status (Library)
  - `GET /archive/transcripts/{key}` -> transcript JSON (segments+speakers)
  - `GET /archive/search?q=&mode=keyword|semantic&k=` -> search hits
  - `GET /archive/stats` -> dashboard metrics
- `scripts/batch_transcribe.py` — CLI that lists the media prefix and transcribes every un-transcribed file via the service layer (demonstrates **bulk** ingest + write-amplification).

Frontend (`apps/web/src/`):
- **`/library`** — **sample-specific asset explorer scoped to `media/`** (the required add): card/table of each media file with size, duration (from transcript when available), transcription status badge, a **Transcribe** action (with live progress), and a link to its transcript. Distinct from the full-bucket `/files` explorer, which stays.
- **`/search`** — search box with keyword/semantic toggle and top-k; results grouped by source file showing speaker, timestamp, snippet, and a jump-to-media affordance.
- **Transcript viewer** — `/library/[key]` (or a drawer) rendering speaker-attributed segments with timestamps; reachable from Library and Search.
- **Dashboard (`/`) ADAPTED** — replace starter stats with archive metrics: files in archive, files transcribed, speakers detected, segments indexed, hours of audio processed, storage used; recent-transcriptions table replaces recent-uploads. New aggregations flow through `runtime->service->repo` and TanStack Query hooks (no bare `useEffect+fetch`).
- Sidebar nav adds **Library** and **Search** (keep Dashboard, Upload, Files, Settings, Design link).
- `packages/shared/src/types.ts` + `lib/api-client.ts` + `lib/queries.ts` extended for every new endpoint (the 3-file rule).

### B2 prefix layout (single bucket)
```
media/                 source audio/video (Upload page writes here)
transcripts/{key}.json word-aligned transcript + speaker labels
segments/{key}.json    speaker segments (text, speaker, start, end)
embeddings/{key}.json  per-segment embedding vectors + segment refs
```
Library/status is derived from B2 listings (transcript exists => transcribed); no application DB — B2 remains the sole data store. Semantic search loads `embeddings/*` and ranks in-process (documented small-archive caveat; a vector DB is the scale path).

## 3. B2 surface (S3-compatible only — Standard #1 OK)
- `put_object` — media upload (existing) + transcript/segment/embedding JSON artifacts (new)
- `get_object` — **new**: download media bytes for processing; read artifacts for search/viewer
- `list_objects_v2` — media list, artifact existence, dashboard stats (existing pattern)
- `head_object` — object metadata (existing)
- `delete_object` — delete (existing)
- `generate_presigned_url` — media playback/download in UI (existing)

All via boto3 S3 client in `repo/`. **No b2-native API anywhere.** Custom UA preserved (see section 6). Standard #2 OK, Standard #1 OK.

## 4. Key features (seed README + `docs/features/*` stubs)
1. **Media library on B2** — upload audio/video; everything lands in B2 first (`media/` prefix); browse it in a scoped Library view.
2. **Word-aligned transcription (WhisperX)** — local, configurable model size; CPU-friendly defaults.
3. **Speaker diarization (pyannote)** — speaker labels per word/segment; free HF token for gated weights; graceful transcribe-only fallback when absent.
4. **Semantic + keyword search** — sentence-transformers embeddings per speaker segment; query the whole archive by meaning or exact terms.
5. **Searchable archive on B2** — transcripts, speaker segments, and embeddings accumulate in B2 as the source library grows (write-amplification story).
6. **Bulk batch processing** — CLI transcribes an entire un-processed library in one pass.

**External API provider (per `api-provider-selection.md`):** the sample's whole
point is a **local OSS** pipeline (api-provider rule 1 -> local is the default; do
not substitute a remote provider). No remote inference API is used.
- Models (all local): WhisperX/faster-whisper (default `base`, configurable), pyannote `speaker-diarization-3.1`, sentence-transformers `all-MiniLM-L6-v2`.
- **Estimated cost for one full demo run: $0** (local compute only).
- **Key/env var:** `HF_TOKEN` — a **free** HuggingFace access token, used *only* to download pyannote's gated weights (no per-call cost, not an inference API). Placeholder in `.env.example`; documented where to get it; never committed. Diarization degrades gracefully to transcribe-only if unset, so the app still runs with B2 creds alone.

## 5. Doc transforms
- **README.md** — full rewrite: purpose, the 6-step ingest->transcribe->diarize->embed->store->search workflow, Quick Start (B2 creds with **Standard #3** names + `pip install -r requirements-ml.txt` + ffmpeg + free HF token + pyannote model-terms acceptance), B2 layout, feature list, commands (add `batch_transcribe`), screenshots placeholder. Keep B2 sign-up links with **renamed UTM** content tag.
- **ARCHITECTURE.md** — add transcription-pipeline components, the `media/transcripts/segments/embeddings` prefixes, transcribe/diarize/embed/search data flows, new repo methods, and the note that ML inference is local compute living in `service/engine/` (only boto3 is confined to `repo/`).
- **AGENTS.md** — update repo map (new routers/services/pages), commands (ML install, batch CLI, HF token), reframe "Building on this starter kit" as the realized contract (kept UI kit / Files / Upload, adapted Dashboard). Keep all layering invariants + mechanical-enforcement table.
- **docs/features/**: KEEP+adapt `file-upload.md` (now media), `file-browser.md` (bucket explorer), `dashboard.md` (archive metrics). DELETE `metadata-extraction.md`. NEW stubs from `_template.md`: `transcription.md` (transcribe+diarize), `search.md` (keyword+semantic+embeddings), `archive-library.md` (scoped Library explorer).
- **docs/SECURITY.md / RELIABILITY.md** — light touch: note HF token handling (free, download-only, never logged), media key prefix-allowlist validation, ephemeral job registry resets on restart, long-running background jobs.
- **infra/railway/README.md** — rename env table to Standard #3 names; note the ML deps + that GPU is recommended for production throughput.

## 6. Rename table

**Identifiers**
| From | To | Kind |
|------|----|------|
| `vibe-coding-starter-kit` | `whisperx-diarized-archive` | kebab slug — root pkg `name`, pnpm `--filter` targets, README clone URLs, lockfile pkg name |
| `@vibe-coding-starter-kit/web` | `@whisperx-diarized-archive/web` | npm workspace package |
| `@vibe-coding-starter-kit/shared` | `@whisperx-diarized-archive/shared` | npm workspace package |
| `Vibe Coding Starter Kit` | `WhisperX Diarized Archive` | Title Case — README/AGENTS/ARCHITECTURE headings |
| `b2ai-oss-start` (boto3 `user_agent_extra`, `b2_client.py:45`) | `whisperx-diarized-archive` | **custom user-agent (Standard #2)** |
| `utm_content=b2ai-oss-start` (README B2 links) | `utm_content=whisperx-diarized-archive` | UTM content tag |
| `b2ai-oss-start` in `scripts/doctor.mjs`, `app-sidebar.tsx` | `whisperx-diarized-archive` | preflight/UI label references |
| Railway `web`/`api` service refs | `whisperx-diarized-archive-web` / `-api` | deploy slugs / image tags |
| Python package `app` | `app` (unchanged — already generic) | — |

**Env vars (Standard #3 — starter kit is non-compliant; this is the documented rename):**
| Starter kit | New (Standard #3) | Note |
|------|------|------|
| `B2_KEY_ID` | `B2_APPLICATION_KEY_ID` | rename in settings, `.env.example`, doctor, README, railway |
| `B2_ENDPOINT` | `B2_REGION` | store region (default `us-west-004`); derive endpoint `https://s3.{B2_REGION}.backblazeb2.com` via a settings property |
| `B2_APPLICATION_KEY` | `B2_APPLICATION_KEY` | unchanged |
| `B2_BUCKET_NAME` | `B2_BUCKET_NAME` | unchanged |
| `B2_PUBLIC_URL` | `B2_PUBLIC_URL_BASE` | rename |

**New env vars:** `HF_TOKEN` (free, diarization weights), `WHISPERX_MODEL` (default `base`), `WHISPERX_DEVICE` (default `cpu`), `WHISPERX_COMPUTE_TYPE` (default `int8`), `WHISPERX_BATCH_SIZE` (default `8`), `DIARIZATION_MODEL` (default `pyannote/speaker-diarization-3.1`), `EMBEDDING_MODEL` (default `sentence-transformers/all-MiniLM-L6-v2`), `ARCHIVE_MEDIA_PREFIX` (default `media/`).

**Dependencies:** base `requirements.txt` keeps FastAPI/boto3 stack, **removes** Pillow + PyPDF2 (+ python-magic unless used). NEW `services/api/requirements-ml.txt`: `whisperx`, `pyannote.audio`, `sentence-transformers`, `torch`, `torchaudio`, `faster-whisper` (lazy-imported; ffmpeg documented as a system dep).

---

### Out-of-scope / accepted caveats (documented, not bugs)
- No GPU assumed: CPU defaults (`base`/`int8`) keep a short clip runnable locally; large libraries want a GPU (noted).
- No vector DB: semantic search loads embeddings from B2 and ranks in-process — fine for a demo archive; vector DB is the scale path.
- Job registry is process-local (live progress only); transcription completion is authoritative from B2 artifacts.
- No bundled binary media (sample audio) — Phase-5 rule forbids creating binary assets; README points users to their own files / a public clip.
