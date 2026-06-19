<!-- last_verified: 2026-06-19 -->
# App Workflows

User journeys inside the application.

## Upload Media

- User navigates to `/upload`
- Drops or selects audio/video files in the dropzone
- Client validates file size (max 500MB) and type (audio/video allowlist)
- Progress bar shows per-file upload status
- On success: toast notification; the file lands in B2 under `media/`
- On failure: red status icon with error message
- See: [Media Upload](features/file-upload.md)

## Build the Archive (Transcribe)

- User navigates to `/library` (scoped to the `media/` prefix)
- Each file shows a transcription-status badge derived from B2 (transcript exists?)
- User clicks **Transcribe** on an un-transcribed file → a background job is enqueued
- The status badge tracks live progress: queued → transcribing → diarizing → embedding → writing → done
- The pipeline writes `transcripts/`, `segments/`, and `embeddings/` artifacts back to B2
- If `HF_TOKEN` is unset, the file is transcribed without speaker labels (transcribe-only) and the badge says so
- See: [Transcription](features/transcription.md), [Archive Library](features/archive-library.md)

## Read a Transcript

- From the Library (or a Search result), user opens `/library/[key]`
- The viewer renders speaker-attributed segments with mm:ss timecodes, color-coded per speaker
- See: [Archive Library](features/archive-library.md)

## Search the Archive

- User navigates to `/search`
- Enters a query and chooses **Keyword** (exact substring) or **Semantic** (meaning, via embeddings)
- Results are grouped by source file, each showing speaker, timestamp, snippet, and a link to the transcript
- See: [Search](features/search.md)

## Browse the Whole Bucket

- User navigates to `/files`
- The full-bucket explorer shows every object — source `media/` plus `transcripts/`, `segments/`, `embeddings/`
- Tree view with preview, download, and delete
- See: [Bucket Explorer (Files)](features/file-browser.md)

## View Dashboard

- User navigates to `/` (home)
- Stat cards show: files in archive, files transcribed, speakers detected, segments indexed, hours processed, storage used
- Recent-transcriptions table shows the last 10 transcribed files, linking to each transcript
- See: [Dashboard](features/dashboard.md)
