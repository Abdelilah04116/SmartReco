"""Storage layer abstractions for datasets, features, and models."""
from __future__ import annotations

import io
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union, BinaryIO

import pandas as pd
from loguru import logger

from .config import settings

try:
    import boto3  # type: ignore
    from botocore.exceptions import ClientError  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    boto3 = None  # type: ignore
    ClientError = Exception  # type: ignore

try:
    from azure.storage.blob import BlobServiceClient  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    BlobServiceClient = None  # type: ignore


class StorageError(RuntimeError):
    """Raised when storage operations fail."""


@dataclass
class StoredArtifact:
    """Descriptor containing information about a stored artifact."""

    uri: str
    backend: str
    metadata: Optional[dict] = None


class StorageManager:
    """Abstracts access to dataset/model storage backends."""

    def __init__(self) -> None:
        self.backend = settings.STORAGE_BACKEND.lower()
        self._ensure_local_dirs()
        logger.info(f"Storage backend initialised: {self.backend}")

    @staticmethod
    def _safe_json_dump(data: dict) -> str:
        return json.dumps(data, indent=2, default=str)

    def _ensure_local_dirs(self) -> None:
        base_dirs = [
            settings.DATA_DIR / settings.NORMALIZED_DATA_SUBDIR,
            settings.DATA_DIR / settings.METADATA_SUBDIR,
            settings.DATA_DIR / settings.FEATURE_STORE_SUBDIR,
            settings.DATA_DIR / settings.MODELS_SUBDIR,
        ]
        for path in base_dirs:
            path.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def save_dataframe(
        self,
        df: pd.DataFrame,
        artifact_name: str,
        subdir: Optional[str] = None,
        format: str = "parquet",
        metadata: Optional[dict] = None,
    ) -> StoredArtifact:
        """Persist a dataframe and associated metadata."""
        if format not in {"parquet", "csv"}:
            raise ValueError("Unsupported dataframe format")

        if self.backend == "local":
            return self._save_dataframe_local(df, artifact_name, subdir, format, metadata)
        if self.backend == "s3":
            return self._save_dataframe_s3(df, artifact_name, subdir, format, metadata)
        if self.backend == "azure_blob":
            return self._save_dataframe_azure(df, artifact_name, subdir, format, metadata)
        raise StorageError(f"Unknown storage backend {self.backend}")

    def load_dataframe(
        self,
        artifact_name: str,
        subdir: Optional[str] = None,
        format: str = "parquet",
    ) -> pd.DataFrame:
        """Load a dataframe artifact."""
        if self.backend == "local":
            return self._load_dataframe_local(artifact_name, subdir, format)
        if self.backend == "s3":
            return self._load_dataframe_s3(artifact_name, subdir, format)
        if self.backend == "azure_blob":
            return self._load_dataframe_azure(artifact_name, subdir, format)
        raise StorageError(f"Unknown storage backend {self.backend}")

    def save_bytes(
        self,
        buffer: Union[bytes, BinaryIO],
        artifact_name: str,
        subdir: Optional[str] = None,
    ) -> StoredArtifact:
        """Persist a generic binary artifact (e.g. model, encoder)."""
        if isinstance(buffer, bytes):
            stream = io.BytesIO(buffer)
        else:
            stream = buffer

        if self.backend == "local":
            return self._save_bytes_local(stream, artifact_name, subdir)
        if self.backend == "s3":
            return self._save_bytes_s3(stream, artifact_name, subdir)
        if self.backend == "azure_blob":
            return self._save_bytes_azure(stream, artifact_name, subdir)
        raise StorageError(f"Unknown storage backend {self.backend}")

    def load_bytes(
        self,
        artifact_name: str,
        subdir: Optional[str] = None,
    ) -> bytes:
        """Load a persisted binary artifact."""
        if self.backend == "local":
            return self._load_bytes_local(artifact_name, subdir)
        if self.backend == "s3":
            return self._load_bytes_s3(artifact_name, subdir)
        if self.backend == "azure_blob":
            return self._load_bytes_azure(artifact_name, subdir)
        raise StorageError(f"Unknown storage backend {self.backend}")

    # ------------------------------------------------------------------
    # Local backend
    # ------------------------------------------------------------------
    def _resolve_local_path(self, artifact_name: str, subdir: Optional[str]) -> Path:
        base_dir = settings.DATA_DIR
        if subdir:
            base_dir = base_dir / subdir
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir / artifact_name

    def _save_dataframe_local(
        self,
        df: pd.DataFrame,
        artifact_name: str,
        subdir: Optional[str],
        format: str,
        metadata: Optional[dict],
    ) -> StoredArtifact:
        path = self._resolve_local_path(
            f"{artifact_name}.{format}",
            subdir or settings.NORMALIZED_DATA_SUBDIR,
        )
        logger.info(f"Persisting dataframe locally at {path}")
        if format == "parquet":
            df.to_parquet(path, index=False)
        else:
            df.to_csv(path, index=False)

        if metadata:
            meta_path = path.with_suffix(".json")
            meta_path.write_text(self._safe_json_dump(metadata))

        return StoredArtifact(uri=str(path), backend="local", metadata=metadata)

    def _load_dataframe_local(
        self,
        artifact_name: str,
        subdir: Optional[str],
        format: str,
    ) -> pd.DataFrame:
        path = self._resolve_local_path(
            f"{artifact_name}.{format}",
            subdir or settings.NORMALIZED_DATA_SUBDIR,
        )
        logger.info(f"Loading dataframe from {path}")
        if not path.exists():
            raise StorageError(f"Artifact not found at {path}")
        if format == "parquet":
            return pd.read_parquet(path)
        return pd.read_csv(path)

    def _save_bytes_local(
        self,
        stream: BinaryIO,
        artifact_name: str,
        subdir: Optional[str],
    ) -> StoredArtifact:
        path = self._resolve_local_path(
            artifact_name,
            subdir or settings.MODELS_SUBDIR,
        )
        logger.info(f"Persisting binary artifact locally at {path}")
        with open(path, "wb") as f:
            f.write(stream.read())
        return StoredArtifact(uri=str(path), backend="local")

    def _load_bytes_local(
        self,
        artifact_name: str,
        subdir: Optional[str],
    ) -> bytes:
        path = self._resolve_local_path(
            artifact_name,
            subdir or settings.MODELS_SUBDIR,
        )
        if not path.exists():
            raise StorageError(f"Artifact not found at {path}")
        with open(path, "rb") as f:
            return f.read()

    # ------------------------------------------------------------------
    # S3 backend
    # ------------------------------------------------------------------
    def _get_s3_client(self):
        if boto3 is None:
            raise StorageError("boto3 is not installed but S3 backend is configured.")
        if not settings.S3_BUCKET:
            raise StorageError("S3 bucket is not configured.")
        session = boto3.session.Session(
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            region_name=settings.S3_REGION,
        )
        return session.client("s3", endpoint_url=settings.S3_ENDPOINT_URL)

    def _build_s3_key(self, artifact_name: str, subdir: Optional[str], extension: Optional[str] = None) -> str:
        key_parts = []
        if subdir:
            key_parts.append(subdir)
        else:
            key_parts.append(settings.NORMALIZED_DATA_SUBDIR)
        name = artifact_name if extension is None else f"{artifact_name}.{extension}"
        key_parts.append(name)
        return "/".join(key_parts)

    def _save_dataframe_s3(
        self,
        df: pd.DataFrame,
        artifact_name: str,
        subdir: Optional[str],
        format: str,
        metadata: Optional[dict],
    ) -> StoredArtifact:
        client = self._get_s3_client()
        buffer = io.BytesIO()
        if format == "parquet":
            df.to_parquet(buffer, index=False)
        else:
            df.to_csv(buffer, index=False)
        buffer.seek(0)
        key = self._build_s3_key(artifact_name, subdir, format)
        logger.info(f"Uploading dataframe to S3 bucket {settings.S3_BUCKET} key {key}")
        try:
            client.upload_fileobj(buffer, settings.S3_BUCKET, key)
            if metadata:
                meta_key = self._build_s3_key(artifact_name, subdir, "json")
                client.put_object(
                    Bucket=settings.S3_BUCKET,
                    Key=meta_key,
                    Body=self._safe_json_dump(metadata).encode("utf-8"),
                )
        except ClientError as exc:  # pragma: no cover - network interaction
            raise StorageError(f"Failed to upload dataframe to S3: {exc}") from exc
        return StoredArtifact(
            uri=f"s3://{settings.S3_BUCKET}/{key}",
            backend="s3",
            metadata=metadata,
        )

    def _load_dataframe_s3(
        self,
        artifact_name: str,
        subdir: Optional[str],
        format: str,
    ) -> pd.DataFrame:
        client = self._get_s3_client()
        key = self._build_s3_key(artifact_name, subdir, format)
        buffer = io.BytesIO()
        try:
            client.download_fileobj(settings.S3_BUCKET, key, buffer)
        except ClientError as exc:  # pragma: no cover
            raise StorageError(f"Failed to download dataframe from S3: {exc}") from exc
        buffer.seek(0)
        if format == "parquet":
            return pd.read_parquet(buffer)
        return pd.read_csv(buffer)

    def _save_bytes_s3(
        self,
        stream: BinaryIO,
        artifact_name: str,
        subdir: Optional[str],
    ) -> StoredArtifact:
        client = self._get_s3_client()
        key = self._build_s3_key(artifact_name, subdir or settings.MODELS_SUBDIR)
        logger.info(f"Uploading binary artifact to S3 key {key}")
        try:
            client.upload_fileobj(stream, settings.S3_BUCKET, key)
        except ClientError as exc:  # pragma: no cover
            raise StorageError(f"Failed to upload bytes to S3: {exc}") from exc
        return StoredArtifact(uri=f"s3://{settings.S3_BUCKET}/{key}", backend="s3")

    def _load_bytes_s3(
        self,
        artifact_name: str,
        subdir: Optional[str],
    ) -> bytes:
        client = self._get_s3_client()
        key = self._build_s3_key(artifact_name, subdir or settings.MODELS_SUBDIR)
        buffer = io.BytesIO()
        try:
            client.download_fileobj(settings.S3_BUCKET, key, buffer)
        except ClientError as exc:  # pragma: no cover
            raise StorageError(f"Failed to download bytes from S3: {exc}") from exc
        buffer.seek(0)
        return buffer.read()

    # ------------------------------------------------------------------
    # Azure Blob backend
    # ------------------------------------------------------------------
    def _get_blob_client(self):
        if BlobServiceClient is None:
            raise StorageError("azure-storage-blob is not installed but Azure backend configured.")
        if not settings.AZURE_BLOB_CONNECTION_STRING or not settings.AZURE_BLOB_CONTAINER:
            raise StorageError("Azure blob storage configuration missing.")
        service_client = BlobServiceClient.from_connection_string(settings.AZURE_BLOB_CONNECTION_STRING)  # type: ignore[no-untyped-call]
        return service_client.get_container_client(settings.AZURE_BLOB_CONTAINER)  # type: ignore[no-any-return]

    def _build_blob_path(self, artifact_name: str, subdir: Optional[str], extension: Optional[str] = None) -> str:
        key_parts = []
        if subdir:
            key_parts.append(subdir)
        else:
            key_parts.append(settings.NORMALIZED_DATA_SUBDIR)
        name = artifact_name if extension is None else f"{artifact_name}.{extension}"
        key_parts.append(name)
        return "/".join(key_parts)

    def _save_dataframe_azure(
        self,
        df: pd.DataFrame,
        artifact_name: str,
        subdir: Optional[str],
        format: str,
        metadata: Optional[dict],
    ) -> StoredArtifact:
        client = self._get_blob_client()
        blob_name = self._build_blob_path(artifact_name, subdir, format)
        buffer = io.BytesIO()
        if format == "parquet":
            df.to_parquet(buffer, index=False)
        else:
            df.to_csv(buffer, index=False)
        buffer.seek(0)
        logger.info(f"Uploading dataframe to Azure blob {blob_name}")
        client.upload_blob(name=blob_name, data=buffer, overwrite=True)
        if metadata:
            meta_blob = self._build_blob_path(artifact_name, subdir, "json")
            client.upload_blob(name=meta_blob, data=self._safe_json_dump(metadata), overwrite=True)
        return StoredArtifact(
            uri=f"azure://{settings.AZURE_BLOB_CONTAINER}/{blob_name}",
            backend="azure_blob",
            metadata=metadata,
        )

    def _load_dataframe_azure(
        self,
        artifact_name: str,
        subdir: Optional[str],
        format: str,
    ) -> pd.DataFrame:
        client = self._get_blob_client()
        blob_name = self._build_blob_path(artifact_name, subdir, format)
        downloader = client.download_blob(blob_name)
        buffer = io.BytesIO(downloader.readall())
        if format == "parquet":
            return pd.read_parquet(buffer)
        return pd.read_csv(buffer)

    def _save_bytes_azure(
        self,
        stream: BinaryIO,
        artifact_name: str,
        subdir: Optional[str],
    ) -> StoredArtifact:
        client = self._get_blob_client()
        blob_name = self._build_blob_path(artifact_name, subdir or settings.MODELS_SUBDIR)
        logger.info(f"Uploading binary artifact to Azure blob {blob_name}")
        client.upload_blob(name=blob_name, data=stream, overwrite=True)
        return StoredArtifact(uri=f"azure://{settings.AZURE_BLOB_CONTAINER}/{blob_name}", backend="azure_blob")

    def _load_bytes_azure(
        self,
        artifact_name: str,
        subdir: Optional[str],
    ) -> bytes:
        client = self._get_blob_client()
        blob_name = self._build_blob_path(artifact_name, subdir or settings.MODELS_SUBDIR)
        downloader = client.download_blob(blob_name)
        return downloader.readall()


storage_manager = StorageManager()






