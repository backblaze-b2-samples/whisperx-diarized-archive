<!-- last_verified: 2026-06-19 -->
# Security

Security principles and implementation for whisperx-diarized-archive.

## Trust Boundaries

- **Frontend -> API**: CORS-restricted to configured origins, scoped to `GET/POST/DELETE/OPTIONS`
- **API -> B2**: Authenticated via `B2_APPLICATION_KEY_ID` + `B2_APPLICATION_KEY`, signature v4
- **Client -> B2**: Presigned URLs for download (10-min expiry, `Content-Disposition: attachment`)
- **API -> HuggingFace Hub**: download-only, to fetch pyannote's gated weights once. The `HF_TOKEN` is free and never an inference credential.

## HuggingFace Token Handling

- `HF_TOKEN` is **free** and used only to download gated diarization weights — never billed, never an inference API
- Loaded via env var (pydantic-settings); never committed; never logged
- Optional: when unset, diarization is skipped (transcribe-only) — the app still runs with B2 creds alone

## Upload Validation

- Filename sanitization: path traversal, null bytes, unsafe chars stripped
- MIME/extension consistency check against the audio/video allowlist
- Chunked streaming with size enforcement (500MB default)
- Content-type allowlist (audio/video only)
- Empty file rejection
- Media is written under the `media/` prefix; the Library and batch CLI iterate exactly this prefix

## File Key Validation

- Empty keys rejected
- Path traversal patterns rejected (`../`, `%2e%2e`, backslashes, null bytes)
- The bucket is the only access boundary — add prefix scoping in
  `services/api/app/service/files.py::validate_key` if your deployment
  shares a bucket with other workloads

## Download Safety

- Presigned URLs force `Content-Disposition: attachment`
- Prevents inline rendering of user-uploaded content (XSS mitigation)

## Secrets Management

- All secrets loaded via environment variables (pydantic-settings)
- Never committed to source control
- `.env.example` documents required variables without values

## Agent Security Rules

- Never commit `.env`, credentials, or API keys
- Never weaken validation without explicit instruction
- Never bypass CORS, auth, or input sanitization
- Always validate at system boundaries
