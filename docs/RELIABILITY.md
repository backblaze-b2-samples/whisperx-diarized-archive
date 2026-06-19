<!-- last_verified: 2026-06-19 -->
# Reliability

Reliability expectations and practices for this project.

## Health Checks

- `GET /health` verifies B2 connectivity and returns `healthy` or `degraded`
- Health endpoint is always available, even when B2 is down

## Error Handling

- HTTP handlers return structured error responses with appropriate status codes
- External service failures (B2) are caught and surfaced as 500/503 responses
- No unhandled exceptions leak stack traces to clients

## Logging

- Structured JSON logging via Python stdlib
- Every request gets a `request_id` for tracing
- Log levels: ERROR for failures, WARNING for degraded state, INFO for requests

## Observability

- Request timing middleware logs duration for every request
- `/metrics` endpoint exposes basic Prometheus-format counters
- Upload success/failure counts tracked

## Graceful Degradation

- File listing returns empty list (not error) when B2 has no objects
- Diarization degrades to transcribe-only when `HF_TOKEN` is unset — the pipeline still completes and produces a transcript
- Word alignment failure falls back to segment-level timestamps (still usable)
- Frontend shows skeleton states while loading, error states on failure

## Long-Running Background Jobs

- Transcription runs as a FastAPI `BackgroundTask`; live progress is tracked in a process-local, **ephemeral** job registry (`service/jobs.py`) that resets on restart
- The authoritative "is this transcribed?" signal is the existence of `transcripts/{key}.json` in B2 — never the job registry
- A failed job is marked `error` with the underlying message; completed artifacts already written to B2 are unaffected
- If the heavy ML stack or ffmpeg is missing, the job errors with an actionable install hint rather than crashing the API

## Deployment

- Railway health checks on `/health`
- Zero-downtime deploys via rolling updates
- Environment-specific configuration via env vars (no config files in prod)
