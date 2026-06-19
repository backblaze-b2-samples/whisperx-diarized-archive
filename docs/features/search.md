<!-- last_verified: 2026-06-19 -->
# Feature: Search

## Purpose
Query the whole transcript archive by exact keyword or by semantic meaning,
returning speaker-attributed segments that link back to their source file.

## Used By
- UI: `/search` page
- API: `GET /archive/search?q=&mode=keyword|semantic&k=`

## Core Functions
- `apps/web/src/components/search/search-panel.tsx` — query box, keyword/semantic toggle, grouped results
- `apps/web/src/lib/queries.ts` — `useArchiveSearch()`
- `services/api/app/runtime/archive.py` — `GET /archive/search` handler
- `services/api/app/service/search.py` — `keyword_search()` (substring) + `semantic_search()` (cosine)
- `services/api/app/service/engine/embed.py` — `embed_query()` for semantic mode (lazy import)
- `services/api/app/repo/archive_store.py` — `list_keys`, `get_json`

## Canonical Files
- Search logic: `services/api/app/service/search.py`

## Inputs
- q: string (the query; required, min length 1)
- mode: "keyword" | "semantic" (default keyword)
- k: int (top-k, 1–100, default 20)

## Outputs
- `GET /archive/search` → `SearchHit[]` (key, segment_index, speaker, start, end, text, score)

## Flow
- Keyword mode: iterate `segments/*` artifacts, case-insensitive substring match over each segment's text
- Semantic mode: embed the query, iterate `embeddings/*` artifacts, score by cosine similarity (vectors are stored L2-normalized so dot product == cosine), sort descending
- The UI groups hits by source file and links each group to its transcript

## Edge Cases
- Empty query → no request fired (hook disabled)
- No artifacts yet → empty result set, empty state in UI
- Semantic mode without the ML stack → `embed_query` raises `MissingMLDependencies` → 503-style error surfaced inline
- Large archive → all embeddings are loaded and ranked in-process (documented small-archive caveat; a vector DB is the scale path)

## UX States
- Idle: nothing rendered until the user submits a query
- Loading: skeleton result cards
- Empty: "No matches"
- Error: inline `ErrorState` with Retry
- Loaded: result cards grouped by file, semantic scores shown as badges

## Verification
- Test files: `services/api/tests/test_search.py`
- Required cases: keyword substring match, semantic cosine ranking, artifact key derivation
- Quick verify command: `pnpm test:api`
- Full verify command: `pnpm lint && pnpm lint:api && pnpm test:api && pnpm check:structure`
- Pass criteria: pytest green (search tests run without the ML stack via mocks)

## Related Docs
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [Transcription](transcription.md)
- [App Workflows](../app-workflows.md)
