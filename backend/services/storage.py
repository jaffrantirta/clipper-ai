import logging
from abc import ABC, abstractmethod
from pathlib import Path

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    @abstractmethod
    def upload(self, local_path: Path, key: str) -> str:
        """Upload a local file and return its public URL."""

    def cleanup(self, local_path: Path) -> None:
        """Remove local file after upload (no-op for local storage)."""


class LocalStorage(StorageBackend):
    """Files stay on disk, served by FastAPI StaticFiles at /clips."""

    def upload(self, local_path: Path, key: str) -> str:
        return f"/clips/{key}"


class S3Storage(StorageBackend):
    """AWS S3 or any S3-compatible service (Cloudflare R2, MinIO, Wasabi, etc.)."""

    def __init__(
        self,
        bucket: str,
        region: str,
        *,
        endpoint_url: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        public_url: str | None = None,
        acl: str | None = "public-read",
    ) -> None:
        import boto3

        self.bucket = bucket
        self.acl = acl
        self._public_base = (public_url or "").rstrip("/")

        kwargs: dict = {"region_name": region}
        if endpoint_url:
            kwargs["endpoint_url"] = endpoint_url
        if access_key:
            kwargs["aws_access_key_id"] = access_key
        if secret_key:
            kwargs["aws_secret_access_key"] = secret_key

        self.client = boto3.client("s3", **kwargs)

        # Derive public URL base if not supplied
        if not self._public_base:
            if endpoint_url:
                self._public_base = f"{endpoint_url.rstrip('/')}/{bucket}"
            else:
                self._public_base = f"https://{bucket}.s3.{region}.amazonaws.com"

    def upload(self, local_path: Path, key: str) -> str:
        extra: dict = {}
        if self.acl:
            extra["ACL"] = self.acl
        self.client.upload_file(str(local_path), self.bucket, key, ExtraArgs=extra or None)
        url = f"{self._public_base}/{key}"
        logger.info("S3 uploaded %s → %s", key, url)
        return url

    def cleanup(self, local_path: Path) -> None:
        local_path.unlink(missing_ok=True)


class GCSStorage(StorageBackend):
    """Google Cloud Storage with public object access."""

    def __init__(self, bucket: str) -> None:
        from google.cloud import storage as gcs  # type: ignore

        self.client = gcs.Client()
        self.bucket = self.client.bucket(bucket)
        self.bucket_name = bucket

    def upload(self, local_path: Path, key: str) -> str:
        blob = self.bucket.blob(key)
        blob.upload_from_filename(str(local_path))
        blob.make_public()
        url = blob.public_url
        logger.info("GCS uploaded %s → %s", key, url)
        return url

    def cleanup(self, local_path: Path) -> None:
        local_path.unlink(missing_ok=True)


def get_storage() -> StorageBackend:
    from backend.config import (
        STORAGE_PROVIDER,
        S3_BUCKET, S3_REGION, S3_ENDPOINT_URL, S3_PUBLIC_URL, S3_ACL,
        AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY,
        GCS_BUCKET,
    )

    if STORAGE_PROVIDER == "s3":
        if not S3_BUCKET:
            raise RuntimeError("S3_BUCKET is required when STORAGE_PROVIDER=s3")
        return S3Storage(
            bucket=S3_BUCKET,
            region=S3_REGION or "us-east-1",
            endpoint_url=S3_ENDPOINT_URL or None,
            access_key=AWS_ACCESS_KEY_ID or None,
            secret_key=AWS_SECRET_ACCESS_KEY or None,
            public_url=S3_PUBLIC_URL or None,
            acl=S3_ACL or None,
        )

    if STORAGE_PROVIDER == "gcs":
        if not GCS_BUCKET:
            raise RuntimeError("GCS_BUCKET is required when STORAGE_PROVIDER=gcs")
        return GCSStorage(bucket=GCS_BUCKET)

    return LocalStorage()
