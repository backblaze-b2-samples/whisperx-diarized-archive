#!/usr/bin/env python
"""Bulk-transcribe every un-processed media file in the archive.

Lists the media/ prefix on B2 and runs the full transcribe -> diarize ->
embed -> store pipeline (via the service layer) for any file that does not
yet have a transcripts/{key}.json artifact. This is the write-amplification
demo: one pass over the source library fans out dense transcript / segment /
embedding artifacts across the bucket.

Run from the repo root:
    pnpm batch:transcribe              # only un-transcribed files
    pnpm batch:transcribe -- --force   # re-transcribe everything

Or directly:
    cd services/api && .venv/bin/python scripts/batch_transcribe.py

Requires the ML stack (requirements-ml.txt) + ffmpeg. The .env at the repo
root supplies B2 credentials and (optionally) HF_TOKEN for diarization.
"""

import argparse
import logging
import sys
from pathlib import Path

# Make `app` importable when run as `python scripts/batch_transcribe.py`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")

from app.config import settings  # noqa: E402
from app.repo import list_files  # noqa: E402
from app.service.engine import is_diarization_available  # noqa: E402
from app.service.transcription import is_transcribed, transcribe_media  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("batch_transcribe")


def main() -> int:
    parser = argparse.ArgumentParser(description="Bulk transcribe the B2 media archive")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-transcribe files that already have a transcript artifact",
    )
    args = parser.parse_args()

    if not is_diarization_available():
        log.warning("HF_TOKEN unset — running transcribe-only (no speaker labels).")

    media = [
        f
        for f in list_files(prefix=settings.archive_media_prefix, max_keys=1000)
        if not f.key.endswith("/")
    ]
    if not media:
        log.info("No media found under prefix %s — upload some files first.", settings.archive_media_prefix)
        return 0

    todo = [f for f in media if args.force or not is_transcribed(f.key)]
    log.info("Found %d media file(s); %d to process.", len(media), len(todo))

    failures = 0
    for i, f in enumerate(todo, start=1):
        log.info("[%d/%d] Transcribing %s", i, len(todo), f.key)
        try:
            transcribe_media(f.key)
        except Exception:  # keep going through the batch
            failures += 1
            log.exception("Failed: %s", f.key)

    log.info("Done. %d succeeded, %d failed.", len(todo) - failures, failures)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
