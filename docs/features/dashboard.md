<!-- last_verified: 2026-06-19 -->
# Feature: Dashboard

## Purpose
Give an at-a-glance overview of the transcript archive: how much media is on
B2, how much of it is transcribed, and what the pipeline has produced.

## Used By
- UI: `/` page (dashboard home)
- API: `GET /archive/stats`, `GET /archive/items`

## Core Functions
- `apps/web/src/components/dashboard/archive-stats-cards.tsx` — 6 stat cards
- `apps/web/src/components/dashboard/recent-transcriptions-table.tsx` — last 10 transcribed files
- `apps/web/src/lib/queries.ts` — `useArchiveStats()`, `useArchiveItems()`
- `services/api/app/runtime/archive.py` — `GET /archive/stats`, `GET /archive/items` handlers
- `services/api/app/service/archive.py` — `get_archive_stats()`, `get_archive_items()` business logic
- `services/api/app/repo/b2_client.py` + `archive_store.py` — B2 listings + artifact reads

## Canonical Files
- Dashboard cards: `apps/web/src/components/dashboard/archive-stats-cards.tsx`
- Stats service logic: `services/api/app/service/archive.py`

## Inputs
- None (dashboard loads data automatically)

## Outputs
- `GET /archive/stats` → `ArchiveStats` (media_files, transcribed_files, speakers_detected, segments_indexed, hours_processed, storage_bytes, storage_human)
- `GET /archive/items` → `ArchiveItem[]` (media list + derived transcription status) for the recent-transcriptions table

## Flow
- Page loads → two parallel API calls (archive stats, archive items)
- Stat cards display files in archive, files transcribed, speakers detected, segments indexed, hours processed, storage used
- Recent-transcriptions table shows the last 10 transcribed files with duration, speakers, and upload date, linking to each transcript
- Metrics are derived live from B2 listings + `transcripts/*` artifacts — there is no application DB

## Edge Cases
- API unavailable → cards surface an inline error with Retry (no fake zeros)
- No media uploaded → cards show zeros, table shows empty state
- Media uploaded but not transcribed → counted in `media_files`, absent from `transcribed_files`
- Large archive → listings paginate through all objects via `ContinuationToken`

## UX States
- Loading: skeleton placeholders for cards and table
- Empty: "Nothing transcribed yet"
- Error: inline `ErrorState` with Retry
- Loaded: populated cards + table

## Verification
- Test files: `services/api/tests/test_archive.py`
- Required cases: stats rollup, items reflect transcription status, empty archive
- Quick verify command: `pnpm test:api`
- Full verify command: `pnpm lint && pnpm lint:api && pnpm test:api && pnpm check:structure`
- Pass criteria: all pytest tests green, no ruff violations

## Related Docs
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [Archive Library](archive-library.md)
- [App Workflows](../app-workflows.md)
