from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Backblaze B2 (Standard #3 env var names) ---
    # Region drives the S3 endpoint; we never store the full endpoint URL,
    # so there is no hardcoded region string anywhere in source.
    b2_region: str = "us-west-004"
    b2_application_key_id: str = ""
    b2_application_key: str = ""
    b2_bucket_name: str = ""
    b2_public_url_base: str = ""

    api_port: int = 8000
    # Explicit allowlist by default — covers Next on :3000 and the
    # fallback :3001 it picks if 3000 is busy. Production deploys should
    # override with the exact frontend origin.
    api_cors_origins: str = "http://localhost:3000,http://localhost:3001"
    # Optional dev-only escape hatch: a regex that matches additional
    # allowed origins. Empty by default — set this to e.g.
    # `^http://localhost:\d+$` to accept any localhost port without
    # listing each one. NEVER ship this to production.
    api_cors_origin_regex: str = ""

    # Upload limits — audio/video source media can be large.
    max_file_size: int = 500 * 1024 * 1024  # 500MB

    # Small durable counters (downloads, etc). Point at a persistent
    # volume in production if you care about surviving restarts.
    download_count_file: str = "data/download_count.json"

    # --- Archive / transcription pipeline ---
    # Single bucket; the Upload page and Library are scoped to this prefix.
    archive_media_prefix: str = "media/"
    # Free HuggingFace token, used ONLY to download pyannote's gated
    # diarization weights. Empty => diarization degrades to transcribe-only.
    hf_token: str = ""
    # Local ML engine knobs — CPU-friendly defaults so a short clip runs
    # without a GPU. Bump model size / switch device to "cuda" for throughput.
    whisperx_model: str = "base"
    whisperx_device: str = "cpu"
    whisperx_compute_type: str = "int8"
    whisperx_batch_size: int = 8
    diarization_model: str = "pyannote/speaker-diarization-3.1"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.api_cors_origins.split(",")]

    @property
    def b2_endpoint(self) -> str:
        """Derive the S3-compatible endpoint from the region.

        Keeping only the region in config means no hardcoded endpoint /
        region string lives anywhere else in the source tree.
        """
        return f"https://s3.{self.b2_region}.backblazeb2.com"


settings = Settings()
