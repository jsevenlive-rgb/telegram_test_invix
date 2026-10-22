import mimetypes
import uuid
from functools import lru_cache
from pathlib import Path

from app.config import get_settings


@lru_cache
def get_s3_client():
    import boto3
    from botocore.client import Config

    settings = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=f"{'https' if settings.minio_secure else 'http'}://{settings.minio_endpoint}",
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def _local_root() -> Path:
    settings = get_settings()
    root = Path(settings.media_root)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _use_local() -> bool:
    return get_settings().storage_backend.lower() == "local"


def ensure_bucket() -> None:
    if _use_local():
        _local_root()
        return
    settings = get_settings()
    client = get_s3_client()
    try:
        client.head_bucket(Bucket=settings.minio_bucket)
    except Exception:
        client.create_bucket(Bucket=settings.minio_bucket)


def public_object_url(key: str) -> str:
    """Prefer API media proxy so Mini App on phones can load images via WEBAPP/BACKEND tunnel."""
    settings = get_settings()
    base = settings.backend_url.rstrip("/")
    return f"{base}/api/media/{key}"


def upload_bytes(
    data: bytes,
    *,
    content_type: str = "image/jpeg",
    filename: str | None = None,
    prefix: str = "products",
) -> tuple[str, str]:
    """Store bytes. Returns (object_key, public_url)."""
    ensure_bucket()

    ext = "jpg"
    if filename and "." in filename:
        ext = filename.rsplit(".", 1)[-1].lower()
    elif "png" in content_type:
        ext = "png"
    elif "webp" in content_type:
        ext = "webp"

    key = f"{prefix}/{uuid.uuid4().hex}.{ext}"

    if _use_local():
        path = _local_root() / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        # sidecar content-type for later reads
        path.with_suffix(path.suffix + ".ctype").write_text(content_type, encoding="utf-8")
        return key, public_object_url(key)

    settings = get_settings()
    client = get_s3_client()
    client.put_object(
        Bucket=settings.minio_bucket,
        Key=key,
        Body=data,
        ContentType=content_type,
    )
    return key, public_object_url(key)


def get_object_bytes(key: str) -> tuple[bytes, str]:
    if _use_local():
        path = _local_root() / key
        if not path.is_file():
            raise FileNotFoundError(key)
        ctype_path = path.with_suffix(path.suffix + ".ctype")
        if ctype_path.is_file():
            content_type = ctype_path.read_text(encoding="utf-8").strip()
        else:
            content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        return path.read_bytes(), content_type

    settings = get_settings()
    client = get_s3_client()
    obj = client.get_object(Bucket=settings.minio_bucket, Key=key)
    body = obj["Body"].read()
    content_type = obj.get("ContentType") or "application/octet-stream"
    return body, content_type
