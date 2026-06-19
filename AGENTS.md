<!-- last_verified: 2026-05-01 -->
# AGENTS.md

This is the authoritative control surface for all coding agents. Read this first.

## 1. Repository Map

```
apps/web/          Next.js 16 frontend (App Router, Tailwind v4, shadcn/ui)
  src/app/         Dashboard (/), upload, library, library/[...key], search, files, settings, design
  src/components/  dashboard/, library/, search/, files/, upload/, layout/, ui/ (generated)
  src/lib/         api-client.ts, queries.ts (TanStack), archive-format.ts
services/api/      FastAPI backend (layered: types/config/repo/service/runtime)
  app/service/engine/   Local ML engine — lazy-imported (transcribe / diarize / embed)
  scripts/         batch_transcribe.py (bulk CLI)
  requirements.txt + requirements-ml.txt   base vs heavy ML stack
packages/shared/   Shared TypeScript types (mirrors Pydantic models)
docs/              System of record (features, workflows, security, reliability)
docs/exec-plans/   Execution plans and tech debt tracker
infra/railway/     Deployment config
```

## 2. The Realized Contract (built on the starter kit)

This app was built on the vibe-coding-starter-kit. The starter contract was honored as follows — keep these distinctions when extending.

**Kept verbatim (do not strip, rename, or edit)**
- **UI kit / design system.** `apps/web/src/components/ui/` (shadcn primitives), the design tokens in `apps/web/src/app/globals.css`, and the `/design` reference page. Build new screens with these primitives; never edit generated `components/ui/` files directly. Restyle via tokens in `globals.css`.
- **Bucket Explorer (Files).** `/files` route, `apps/web/src/app/files/`, and `apps/web/src/components/files/` — the full-bucket browse. Its sidebar entry stays.
- **Upload.** `/upload` route and `apps/web/src/components/upload/` — now the on-ramp for source media, writing to the `media/` prefix.

**Added for this app**
- **Library** (`/library`, `/library/[...key]`) — media-only explorer scoped to `media/`, transcribe action + live progress, transcript viewer.
- **Search** (`/search`) — keyword + semantic search over the archive.
- New backend: `runtime/archive.py`, `service/{transcription,search,archive,jobs}.py`, `service/engine/`, `repo/archive_store.py`, `types/archive.py`.

**Adapted**
- **Dashboard.** `/` and `apps/web/src/components/dashboard/` now show archive metrics (files transcribed, speakers, segments, hours) and recent transcriptions. New aggregations flow through `runtime -> service -> repo` and TanStack Query hooks in `apps/web/src/lib/queries.ts` — no bare `useEffect + fetch`.

**Trimmed**
- Image/PDF metadata extraction (the old `service/metadata.py`, Pillow/PyPDF2 deps, and its doc) — irrelevant to audio/video.

## 3. Architectural Invariants

**Backend layering**: `types` -> `config` -> `repo` -> `service` -> `runtime`

- No backward imports across layers
- No `boto3` outside `repo/` (both `b2_client.py` and `archive_store.py` live there)
- **ML inference is local compute, not storage**: `service/engine/` runs models on bytes the repo fetched; it owns no boto3
- **Heavy ML imports are lazy** (inside engine functions) so the API boots and tests pass without `requirements-ml.txt`
- No business logic in route handlers (`runtime/`)
- All external APIs wrapped in `repo/` adapters
- All request/response data validated at boundary (Pydantic models)
- The only module-level mutable state is the explicitly-ephemeral job registry (`service/jobs.py`); B2 artifacts are authoritative

**Frontend**: shadcn/ui components in `src/components/ui/` are generated — never modify them.

**Data fetching**: every API call flows through TanStack Query hooks in `apps/web/src/lib/queries.ts`. No bare `useEffect + fetch` patterns. New endpoints touch three files: `runtime/<router>.py`, `lib/api-client.ts`, `lib/queries.ts`.

## 4. Quality Expectations

- **DRY** — do not duplicate logic, types, or constants. Extract shared code only when used in 2+ places.
- Structured JSON logging only — no `print()` statements
- No raw SDK calls outside `repo/` layer
- Files stay under 300 lines
- Tests added or updated for every behavior change
- Docs updated in same PR as code changes
- Lint clean before merge
- Prefer boring, composable libraries over clever abstractions
- No implicit type assumptions — use typed models

## 5. Mechanical Enforcement

| Rule | Enforced by |
|------|-------------|
| No backward imports | `tests/test_structure.py::test_no_backward_imports` |
| No boto3 outside repo/ | `tests/test_structure.py::test_boto3_only_in_repo` |
| File size < 300 lines | `tests/test_structure.py::test_file_size_limits` |
| All layers exist | `tests/test_structure.py::test_all_layers_exist` |
| No bare print() | `ruff` rule T20 |
| Import ordering | `ruff` rule I001 |
| Frontend strict equality | `eslint` rule eqeqeq |
| No unused vars | `eslint` + `ruff` rules |

## 6. Commands

```bash
# Run
pnpm dev               # start both frontend and backend
pnpm dev:web           # frontend only
pnpm dev:api           # backend only

# Test & Lint (none of these need the ML stack)
pnpm lint              # frontend lint (eslint)
pnpm build             # frontend type check + build
pnpm lint:api          # backend lint (ruff)
pnpm test:api          # backend tests (pytest)
pnpm check:structure   # structural boundary tests
pnpm test:e2e          # Playwright e2e tests

# Transcription pipeline
pnpm batch:transcribe  # bulk transcribe the un-processed media library

# Enabling the pipeline (one-time)
#   cd services/api && source .venv/bin/activate && pip install -r requirements-ml.txt
#   ffmpeg must be on PATH; HF_TOKEN (free) in .env enables speaker diarization
```

## 7. Agent Workflow

1. Read this file first.
2. Review [ARCHITECTURE.md](ARCHITECTURE.md) before structural changes.
3. For non-trivial changes, create a plan in `docs/exec-plans/active/`.
4. Implement the smallest coherent change.
5. Run: `pnpm lint && pnpm lint:api && pnpm test:api && pnpm check:structure`
6. Update docs in the same PR (see §9).
7. Move completed plans to `docs/exec-plans/completed/`.
8. Only change files relevant to the task. No drive-by improvements.

## 8. Frontend Conventions

See [docs/dev-workflows.md](docs/dev-workflows.md) for full details.

## 9. Doc Update Mapping

| Change Type | Update Location |
|-------------|-----------------|
| Feature logic, inputs, outputs, tests | `docs/features/<feature>.md` |
| User journeys | `docs/app-workflows.md` |
| System layout, deployments | `ARCHITECTURE.md` |
| Dev or testing process | `docs/dev-workflows.md` |
| Setup or scope changes | `README.md` |
| Security changes | `docs/SECURITY.md` |
| Reliability changes | `docs/RELIABILITY.md` |
| Active work plans | `docs/exec-plans/active/` |
| Known tech debt | `docs/exec-plans/tech-debt-tracker.md` |

If documentation and implementation conflict, update docs in the same PR. Documentation rot destroys agent reliability.

## 10. Doc Map

| Topic | Location |
|-------|----------|
| System layout, data flows, boundaries | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Feature docs | [docs/features/](docs/features/) |
| User journeys | [docs/app-workflows.md](docs/app-workflows.md) |
| Engineering workflows and testing | [docs/dev-workflows.md](docs/dev-workflows.md) |
| Security principles | [docs/SECURITY.md](docs/SECURITY.md) |
| Reliability expectations | [docs/RELIABILITY.md](docs/RELIABILITY.md) |
| Execution plans | [docs/exec-plans/](docs/exec-plans/) |
| Tech debt | [docs/exec-plans/tech-debt-tracker.md](docs/exec-plans/tech-debt-tracker.md) |

## 11. When Unsure

- Prefer boring, stable libraries
- Prefer small PRs over large changes
- Add tests with every change
- Never bypass lint rules without explicit instruction
- Ask before making destructive or irreversible changes
