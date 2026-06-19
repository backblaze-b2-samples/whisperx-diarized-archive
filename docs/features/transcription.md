<!-- last_verified: 2026-06-19 -->
# Feature: Transcription & Diarization

## Purpose
Turn one media file on B2 into a word-aligned, speaker-attributed transcript
plus per-segment embeddings — all with a local OSS pipeline, fanning the
results back out to B2 (the write-amplification story).

## Used By
- UI: `/library` (Transcribe action + live progress), `/library/[...key]` (transcript viewer)
- API: `POST /archive/transcribe`, `GET /archive/jobs`, `GET /archive/jobs/{id}`, `GET /archive/transcripts/{key}`
- Job: FastAPI `BackgroundTask` running `service/transcription.run_job`
- CLI: `services/api/scripts/batch_transcribe.py` (bulk)

## Core Functions
- `services/api/app/service/transcription.py` — orchestrates download → transcribe → diarize → embed → write
- `services/api/app/service/engine/transcribe.py` — WhisperX word-aligned transcription (lazy import)
- `services/api/app/service/engine/diarize.py` — pyannote speaker labels; graceful transcribe-only fallback when `HF_TOKEN` is unset
- `services/api/app/service/engine/embed.py` — sentence-transformers embedding per segment
- `services/api/app/service/jobs.py` — ephemeral, process-local job registry (live progress)
- `services/api/app/repo/archive_store.py` — `get_object_bytes`, `put_json`, `object_exists`

## Canonical Files
- Pipeline orchestration: `services/api/app/service/transcription.py`
- Engine (lazy ML): `services/api/app/service/engine/`

## Inputs
- key: string (a `media/...` object key)

## Outputs
- `transcripts/{key}.json` — `Transcript` (language, duration, speakers, word-aligned segments)
- `segments/{key}.json` — speaker segments (text, speaker, start, end)
- `embeddings/{key}.json` — one vector per segment + segment refs
- Side effects: three artifacts written to B2; live `TranscriptionJob` progress

## Flow
- `POST /archive/transcribe {key}` validates the key and enqueues a background job (returns the job)
- The job pulls media bytes from B2 (`get_object_bytes`)
- WhisperX transcribes and force-aligns words (`WHISPERX_MODEL`, CPU defaults)
- If `HF_TOKEN` is set, pyannote diarizes and speakers are assigned to segments; otherwise it stays transcribe-only with a clear warning
- sentence-transformers embeds every segment
- The three artifacts are written to B2; the job is marked `done`
- The authoritative "transcribed?" signal is the existence of `transcripts/{key}.json`, not the job registry (which resets on restart)

## Edge Cases
- `HF_TOKEN` unset → diarization skipped, transcript still produced (no speaker labels)
- ML stack not installed → engine raises `MissingMLDependencies`; the job is marked `error` with an install hint
- ffmpeg missing → decode fails; job errors with the underlying message
- Re-transcribe → overwrites artifacts (B2 versions them automatically)
- API restart mid-job → live progress is lost; completed artifacts in B2 are unaffected

## UX States
- Empty: media not yet transcribed → "Not transcribed" badge + Transcribe button
- Loading: status badge cycles queued → transcribing → diarizing → embedding → writing with a percentage
- Error: red badge; retry from the Library
- Done: "Transcribed" / "Diarized" badge + "View transcript"

## Verification
- Test files: `services/api/tests/test_archive.py`, `services/api/tests/test_search.py`
- Required cases: enqueue job, reject bad key, transcript-not-found, artifact key derivation (these run without the ML stack via mocks)
- Quick verify command: `pnpm test:api`
- Full verify command: `pnpm lint && pnpm lint:api && pnpm test:api && pnpm check:structure`
- Pass criteria: pytest green; API boots without `requirements-ml.txt`
- End-to-end (manual, needs ML stack + ffmpeg): upload a clip, click Transcribe, watch progress, open the transcript

## Related Docs
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [Search](search.md)
- [Archive Library](archive-library.md)
- [App Workflows](../app-workflows.md)
