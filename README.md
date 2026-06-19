<!-- last_verified: 2026-06-19 -->
# WhisperX Diarized Archive

Drop an audio/video library into **[Backblaze B2](https://www.backblaze.com/sign-up/ai-cloud-storage?utm_source=github&utm_medium=referral&utm_campaign=ai_artifacts&utm_content=whisperx-diarized-archive)** and turn it into a **searchable, speaker-labeled transcript archive** — entirely on local open-source models.

Source media lands in B2 first. A local pipeline then transcribes each file with **WhisperX** (word-aligned), assigns speaker labels with **pyannote**, embeds every speaker segment with **sentence-transformers**, and writes transcripts, speaker-segment files, and an embedding index back to B2. A web UI lets you browse the media library, watch transcription progress, read speaker-attributed transcripts, and **search the whole archive by keyword or semantic similarity**.

Built for **podcast producers, compliance teams, and content researchers** who want their recordings to become a queryable knowledge base — not just files in a bucket.

## Why B2

This sample is a **write-amplification** story: one uploaded media file fans out into dense, continuously-accumulating transcript / segment / embedding artifacts across a growing archive — all on B2 via the **S3-compatible API**, with a custom user-agent and standard `B2_*` env vars. There is no application database; B2 is the sole data store, and the existence of a `transcripts/{key}.json` object is the authoritative "is this transcribed?" signal.

## The workflow

```
1. Ingest      Upload audio/video → lands in B2 under media/
2. Transcribe  WhisperX produces a word-aligned transcript (local, CPU-friendly)
3. Diarize     pyannote assigns speaker labels per word/segment (free HF token)
4. Embed       sentence-transformers embeds each speaker segment
5. Store       transcripts/, segments/, embeddings/ written back to B2
6. Search      query the whole archive by keyword or semantic similarity
```

## B2 layout (single bucket)

```
media/                 source audio/video (Upload page writes here)
transcripts/{key}.json word-aligned transcript + speaker labels
segments/{key}.json    speaker segments (text, speaker, start, end)
embeddings/{key}.json  per-segment embedding vectors + segment refs
```

## Features

- **Media library on B2** — upload audio/video; browse it in a scoped Library view
- **Word-aligned transcription (WhisperX)** — local, configurable model size, CPU-friendly defaults
- **Speaker diarization (pyannote)** — speaker labels per segment; graceful transcribe-only fallback when no HF token
- **Semantic + keyword search** — query the archive by meaning (embeddings) or exact terms
- **Searchable archive on B2** — transcripts, segments, and embeddings accumulate as the library grows
- **Bulk batch processing** — a CLI transcribes an entire un-processed library in one pass
- **Bucket Explorer** — a full-bucket browser (preview / download / delete) alongside the scoped Library

## Quick Start

You need: Node.js >= 20, pnpm >= 9, Python >= 3.11, **ffmpeg**, a free **[Backblaze B2 account](https://www.backblaze.com/sign-up/ai-cloud-storage?utm_source=github&utm_medium=referral&utm_campaign=ai_artifacts&utm_content=whisperx-diarized-archive)**, and (optional, for speaker labels) a **free** HuggingFace token.

**1. Install frontend dependencies**

```bash
pnpm install
```

**2. Set up the backend**

```bash
cd services/api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt        # base API stack
cd ../..
```

The API boots and tests run with just the base stack. Install the heavy ML stack only when you want to actually transcribe:

```bash
cd services/api && source .venv/bin/activate
pip install -r requirements-ml.txt     # whisperx, pyannote, torch, sentence-transformers
# system dep: ffmpeg must be on PATH (macOS: `brew install ffmpeg`)
cd ../..
```

**3. Add your B2 credentials**

```bash
cp .env.example .env
```

Open `.env` and fill in, from the [Backblaze B2 dashboard](https://secure.backblaze.com/b2_buckets.htm?utm_source=github&utm_medium=referral&utm_campaign=ai_artifacts&utm_content=whisperx-diarized-archive):

1. **Create a bucket** → paste its name into `B2_BUCKET_NAME`. Set `B2_REGION` to your bucket's region (e.g. `us-west-004`); the S3 endpoint is derived from it.
2. **Create an application key** with `Read and Write` permission → `B2_APPLICATION_KEY_ID` and `B2_APPLICATION_KEY` (the key is shown once).

> Walkthroughs: [creating a bucket](https://www.backblaze.com/docs/cloud-storage-create-and-manage-buckets?utm_source=github&utm_medium=referral&utm_campaign=ai_artifacts&utm_content=whisperx-diarized-archive) and [creating app keys](https://www.backblaze.com/docs/cloud-storage-create-and-manage-app-keys?utm_source=github&utm_medium=referral&utm_campaign=ai_artifacts&utm_content=whisperx-diarized-archive).

**4. (Optional) Enable speaker diarization**

Diarization uses pyannote's gated weights. To enable it:

1. Create a **free** token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) and set `HF_TOKEN` in `.env`.
2. Accept the model terms for [`pyannote/speaker-diarization-3.1`](https://huggingface.co/pyannote/speaker-diarization-3.1) and [`pyannote/segmentation-3.0`](https://huggingface.co/pyannote/segmentation-3.0) on HuggingFace.

If `HF_TOKEN` is unset, the app still runs end-to-end and transcribes — it just skips speaker labels (transcribe-only) and tells you so. No B2-only run is blocked by the missing token.

**5. Run it**

```bash
pnpm dev
```

Frontend at `localhost:3000`, API at `localhost:8000`. `pnpm dev` runs `pnpm doctor` first — a preflight that catches setup gotchas (wrong Node/Python, missing venv, missing/placeholder `.env`, busy ports). Run it any time with `pnpm doctor`.

**6. Try it**

Upload a clip on `/upload`, open `/library`, click **Transcribe**, watch the progress, then read the transcript and search the archive. Or transcribe an entire un-processed library at once:

```bash
pnpm batch:transcribe              # only un-transcribed files
pnpm batch:transcribe -- --force   # re-transcribe everything
```

> **No sample media is bundled.** Bring your own short audio/video clip (e.g. an MP3 of a two-person conversation), or grab a public-domain clip such as a [LibriVox](https://librivox.org/) recording or a Creative-Commons podcast episode. A 1–2 minute clip transcribes quickly on CPU with the default `base` model.

## Commands

| Command | What it does |
|---------|-------------|
| `pnpm dev` | Start frontend + backend (runs `pnpm doctor` first) |
| `pnpm dev:web` | Frontend only |
| `pnpm dev:api` | Backend only |
| `pnpm build` | Build frontend |
| `pnpm lint` | Lint frontend |
| `pnpm lint:api` | Lint backend (ruff) |
| `pnpm test:api` | Run backend tests (no ML stack needed) |
| `pnpm check:structure` | Verify layering rules (boto3-in-repo, no backward imports, file size) |
| `pnpm batch:transcribe` | Bulk transcribe the un-processed media library |
| `pnpm test:e2e` | Playwright e2e tests (run `pnpm --filter @whisperx-diarized-archive/web exec playwright install chromium` once first) |

## Models & cost

All models run **locally**; the only external credential beyond B2 is the **free** download-only HuggingFace token.

| Step | Model (default) | Configurable via |
|------|-----------------|------------------|
| Transcription | WhisperX / faster-whisper `base` | `WHISPERX_MODEL`, `WHISPERX_DEVICE`, `WHISPERX_COMPUTE_TYPE` |
| Diarization | `pyannote/speaker-diarization-3.1` | `DIARIZATION_MODEL`, `HF_TOKEN` |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` | `EMBEDDING_MODEL` |

**Estimated cost for a full demo run: $0** (local compute only). CPU defaults keep a short clip runnable; a GPU (`WHISPERX_DEVICE=cuda`) is recommended for large libraries.

## Tech Stack

- TypeScript, Next.js 16, React 19, Tailwind v4, shadcn/ui
- TanStack Query — caching, dedup, retry for every fetch
- Python 3.11+, FastAPI, boto3, Pydantic v2
- WhisperX, pyannote.audio, sentence-transformers, torch (lazy-imported ML stack)
- Backblaze B2 (S3-compatible object storage)
- pnpm workspaces (monorepo)

## Documentation Map

| Doc | Purpose |
|-----|---------|
| [AGENTS.md](AGENTS.md) | Agent table of contents — start here |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System layout, layering, data flows, B2 prefix layout |
| [docs/features/](docs/features/) | Feature docs (upload, transcription, search, library, files, dashboard) |
| [docs/design-system.md](docs/design-system.md) | Design tokens, primitives, loader, error/empty states |
| [docs/app-workflows.md](docs/app-workflows.md) | User journeys |
| [docs/dev-workflows.md](docs/dev-workflows.md) | Engineering workflows and testing |
| [docs/SECURITY.md](docs/SECURITY.md) | Security principles |
| [docs/RELIABILITY.md](docs/RELIABILITY.md) | Reliability expectations |

## License

MIT License - see [LICENSE](LICENSE) for details.

## Claude Agent B2 Skill

Manage Backblaze B2 from your terminal using natural language (list/search, audits, stale or large file detection, security checks, safe cleanup).

Repo: [https://github.com/backblaze-b2-samples/claude-skill-b2-cloud-storage](https://github.com/backblaze-b2-samples/claude-skill-b2-cloud-storage)
