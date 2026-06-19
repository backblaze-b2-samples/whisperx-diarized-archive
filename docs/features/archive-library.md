<!-- last_verified: 2026-06-19 -->
# Feature: Archive Library

## Purpose
Browse the source media in the archive (scoped to the `media/` prefix), see
each file's transcription status, trigger transcription with live progress,
and jump to its transcript. This is the app-specific, media-only view — the
full-bucket view is the [Bucket Explorer (Files)](file-browser.md).

## Used By
- UI: `/library` page, `/library/[...key]` transcript viewer
- API: `GET /archive/items`, `GET /archive/jobs`, `POST /archive/transcribe`, `GET /archive/transcripts/{key}`

## Core Functions
- `apps/web/src/components/library/media-library.tsx` — media table, status badges, Transcribe action, live progress
- `apps/web/src/components/library/transcript-viewer.tsx` — speaker-attributed transcript with timecodes
- `apps/web/src/lib/queries.ts` — `useArchiveItems()`, `useJobs()`, `useStartTranscription()`, `useTranscript()`
- `services/api/app/service/archive.py` — `get_archive_items()`, `get_transcript()`
- `services/api/app/service/jobs.py` — live job progress

## Canonical Files
- Library component: `apps/web/src/components/library/media-library.tsx`
- Library/items service: `services/api/app/service/archive.py`

## Inputs
- None for the list; `key` (a `media/...` object key) for the transcript viewer

## Outputs
- `GET /archive/items` → `ArchiveItem[]` (file + size + duration + transcription status + speaker count)
- `GET /archive/transcripts/{key}` → `Transcript`
- Side effects: `POST /archive/transcribe` enqueues a background job

## Flow
- Library lists `media/` files; for each, transcription status is derived from whether `transcripts/{key}.json` exists in B2
- An un-transcribed file shows a Transcribe button; clicking it enqueues a job and the badge tracks live progress (the page polls `GET /archive/jobs` while jobs are active)
- A transcribed file shows a status badge (Transcribed / Diarized) and a "View transcript" link
- The transcript viewer renders speaker-attributed segments with mm:ss timecodes, color-coded per speaker

## Edge Cases
- Folder-marker objects (keys ending in `/`) are skipped
- File transcribed but transcript fetch fails → inline error with Retry
- Transcribe clicked twice → the API returns the existing active job (no double-enqueue)
- HF token unset → transcripts show a "transcribe-only" badge (no speakers)

## UX States
- Empty: "No media yet" with an Upload prompt
- Loading: skeleton rows
- Error: inline `ErrorState` with Retry
- Loaded: table with status badges and actions

## Verification
- Test files: `services/api/tests/test_archive.py`
- Required cases: items reflect transcription status, transcript-not-found, enqueue + reject bad key
- Quick verify command: `pnpm test:api`
- Full verify command: `pnpm lint && pnpm lint:api && pnpm test:api && pnpm check:structure`
- Pass criteria: pytest green; `pnpm build` compiles `/library` and `/library/[...key]`

## Related Docs
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [Transcription](transcription.md)
- [Bucket Explorer (Files)](file-browser.md)
- [App Workflows](../app-workflows.md)
