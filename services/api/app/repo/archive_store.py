"""B2 data-access helpers for the transcript archive.

Confined to repo/ alongside b2_client.py so boto3 never leaks into higher
layers. These cover the read/write surface the transcription pipeline and
search need beyond the file-management basics in b2_client.py:

- get_object_bytes(key)  -> download source media for local processing
- put_json(key, obj)     -> write transcript / segment / embedding artifacts
- get_json(key)          -> read an artifact back (search, viewer)
- object_exists(key)     -> authoritative "is this transcribed?" check
- list_keys(prefix)      -> bare key listing for batch / artifact iteration
"""

import json

from botocore.exceptions import ClientError

from app.config import settings
from app.repo.b2_client import get_s3_client


def get_object_bytes(key: str) -> bytes:
    """Download an object's full body. Raises RuntimeError on S3 failure."""
    client = get_s3_client()
    try:
        response = client.get_object(Bucket=settings.b2_bucket_name, Key=key)
        return response["Body"].read()
    except ClientError as e:
        raise RuntimeError(f"B2 get_object failed for '{key}': {e}") from e


def put_json(key: str, obj: dict) -> None:
    """Serialize and store a JSON artifact. Raises RuntimeError on failure."""
    client = get_s3_client()
    body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    try:
        client.put_object(
            Bucket=settings.b2_bucket_name,
            Key=key,
            Body=body,
            ContentType="application/json",
        )
    except ClientError as e:
        raise RuntimeError(f"B2 put_object failed for '{key}': {e}") from e


def get_json(key: str) -> dict | None:
    """Read a JSON artifact. Returns None if the key does not exist."""
    client = get_s3_client()
    try:
        response = client.get_object(Bucket=settings.b2_bucket_name, Key=key)
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if code in ("404", "NoSuchKey"):
            return None
        raise
    return json.loads(response["Body"].read())


def object_exists(key: str) -> bool:
    """True if the object exists. The authoritative 'transcribed?' signal."""
    client = get_s3_client()
    try:
        client.head_object(Bucket=settings.b2_bucket_name, Key=key)
        return True
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if code in ("404", "NoSuchKey"):
            return False
        raise


def list_keys(prefix: str = "", max_keys: int = 1000) -> list[str]:
    """Return bare object keys under a prefix, paginating through all pages."""
    client = get_s3_client()
    keys: list[str] = []
    kwargs: dict = {
        "Bucket": settings.b2_bucket_name,
        "Prefix": prefix,
        "MaxKeys": max_keys,
    }
    try:
        while True:
            response = client.list_objects_v2(**kwargs)
            keys.extend(obj["Key"] for obj in response.get("Contents", []))
            if not response.get("IsTruncated"):
                break
            kwargs["ContinuationToken"] = response["NextContinuationToken"]
    except ClientError as e:
        raise RuntimeError(f"B2 list failed for prefix '{prefix}': {e}") from e
    return keys
