"""Document byte storage behind an interface (DOC-01, DOC-05). Local directory by default, S3-compatible optional."""
import asyncio
import os
import re
from pathlib import Path
from typing import Optional, Protocol

from app.core.config import settings

_KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.\-]*(/[A-Za-z0-9][A-Za-z0-9_.\-]*)*$")


class StorageError(Exception):
    pass


class StorageNotConfigured(StorageError):
    pass


class DocumentStorage(Protocol):
    backend: str

    async def put(self, key: str, data: bytes) -> None: ...

    async def get(self, key: str) -> bytes: ...

    async def exists(self, key: str) -> bool: ...

    async def signed_url(self, key: str, ttl_seconds: int) -> Optional[str]: ...


def validate_key(key: str) -> str:
    if not _KEY_RE.match(key) or ".." in key.split("/"):
        raise StorageError("Invalid storage key")
    return key


class LocalDocumentStorage:
    backend = "local"

    def __init__(self, root: str):
        self.root = Path(root).resolve()

    def _path(self, key: str) -> Path:
        path = (self.root / validate_key(key)).resolve()
        if self.root not in path.parents:
            raise StorageError("Storage key escapes the storage root")
        return path

    def _put(self, key: str, data: bytes) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        with open(tmp, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)

    def _get(self, key: str) -> bytes:
        try:
            return self._path(key).read_bytes()
        except FileNotFoundError as exc:
            raise StorageError("Stored bytes not found") from exc

    async def put(self, key: str, data: bytes) -> None:
        await asyncio.to_thread(self._put, key, data)

    async def get(self, key: str) -> bytes:
        return await asyncio.to_thread(self._get, key)

    async def exists(self, key: str) -> bool:
        return await asyncio.to_thread(lambda: self._path(key).is_file())

    async def signed_url(self, key: str, ttl_seconds: int) -> Optional[str]:
        return None  # local files are only served through the authenticated API download route


class S3DocumentStorage:
    backend = "s3"

    def __init__(self, bucket: str):
        try:
            import boto3  # type: ignore
        except ImportError as exc:
            raise StorageNotConfigured(
                "DISHA_DOCUMENTS_S3_BUCKET is set but boto3 is not installed (pip install -e 'api[s3]')"
            ) from exc
        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.DISHA_DOCUMENTS_S3_ENDPOINT_URL or None,
            region_name=settings.DISHA_DOCUMENTS_S3_REGION or None,
            aws_access_key_id=settings.DISHA_DOCUMENTS_S3_ACCESS_KEY_ID or None,
            aws_secret_access_key=settings.DISHA_DOCUMENTS_S3_SECRET_ACCESS_KEY or None,
        )

    async def put(self, key: str, data: bytes) -> None:
        validate_key(key)
        await asyncio.to_thread(self.client.put_object, Bucket=self.bucket, Key=key, Body=data)

    async def get(self, key: str) -> bytes:
        validate_key(key)

        def _get() -> bytes:
            return self.client.get_object(Bucket=self.bucket, Key=key)["Body"].read()

        try:
            return await asyncio.to_thread(_get)
        except Exception as exc:  # botocore errors
            raise StorageError("Stored bytes not found or unreadable") from exc

    async def exists(self, key: str) -> bool:
        validate_key(key)
        try:
            await asyncio.to_thread(self.client.head_object, Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False

    async def signed_url(self, key: str, ttl_seconds: int) -> Optional[str]:
        validate_key(key)
        return await asyncio.to_thread(
            self.client.generate_presigned_url,
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=ttl_seconds,
        )


_override: Optional[DocumentStorage] = None


def set_storage_override(storage: Optional[DocumentStorage]) -> None:
    """Test hook / explicit injection."""
    global _override
    _override = storage


def get_storage() -> DocumentStorage:
    if _override is not None:
        return _override
    if settings.DISHA_DOCUMENTS_S3_BUCKET:
        return S3DocumentStorage(settings.DISHA_DOCUMENTS_S3_BUCKET)
    return LocalDocumentStorage(settings.DISHA_DOCUMENTS_STORAGE_DIR)
