from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from datetime import date, datetime
from pathlib import Path
from typing import Any


# ── Module-level key-generation (pure string ops, backend-agnostic) ──────────


def normalize_endpoint(endpoint: str) -> str:
    return endpoint.strip("/").replace("/", "_")


def idempotency_key_from_parts(*parts: object) -> str:
    raw = "|".join(str(part) for part in parts).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def idempotency_key(endpoint: str, fixture_id: int, season: int, dt: date) -> str:
    return idempotency_key_from_parts(endpoint, fixture_id, season, dt.isoformat())


def marker_key(league_id: int, season: int, endpoint: str, dt: date, idem_key: str) -> str:
    ep = normalize_endpoint(endpoint)
    return (
        f"state/source=api_football/league={league_id}/season={season}/"
        f"endpoint={ep}/dt={dt.isoformat()}/idempotency_key={idem_key}.json"
    )


def marker_key_without_date(league_id: int, season: int, endpoint: str, idem_key: str) -> str:
    ep = normalize_endpoint(endpoint)
    return (
        f"state/source=api_football/league={league_id}/season={season}/"
        f"endpoint={ep}/idempotency_key={idem_key}.json"
    )


# ── Abstract base class ─────────────────────────────────────────────────────


class StorageWriter(ABC):
    @abstractmethod
    def marker_exists(self, key: str) -> bool: ...

    @abstractmethod
    def put_marker(self, key: str, body: dict[str, Any]) -> None: ...

    @abstractmethod
    def put_raw(
        self,
        league_id: int,
        season: int,
        endpoint: str,
        dt: date,
        run_id: str,
        part: int,
        body: dict[str, Any],
    ) -> str: ...


# ── LocalFileWriter ─────────────────────────────────────────────────────────


class LocalFileWriter(StorageWriter):
    def __init__(self, root: str | Path = "data_lake") -> None:
        self.root = Path(root)

    def marker_exists(self, key: str) -> bool:
        return (self.root / key).exists()

    def put_marker(self, key: str, body: dict[str, Any]) -> None:
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(body), encoding="utf-8")

    def put_raw(
        self,
        league_id: int,
        season: int,
        endpoint: str,
        dt: date,
        run_id: str,
        part: int,
        body: dict[str, Any],
    ) -> str:
        ep = normalize_endpoint(endpoint)
        key = (
            f"raw/source=api_football/league={league_id}/season={season}/"
            f"endpoint={ep}/dt={dt.isoformat()}/run_id={run_id}/part-{part:05d}.json"
        )
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(body), encoding="utf-8")
        return key


# ── S3Writer ─────────────────────────────────────────────────────────────────


class S3Writer(StorageWriter):
    def __init__(self, bucket: str, region: str) -> None:
        import boto3

        self.bucket = bucket
        self.s3 = boto3.client("s3", region_name=region)

    def marker_exists(self, key: str) -> bool:
        from botocore.exceptions import ClientError

        try:
            self.s3.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError as err:
            code = err.response.get("Error", {}).get("Code")
            if code in {"404", "NoSuchKey", "NotFound"}:
                return False
            raise

    def put_marker(self, key: str, body: dict[str, Any]) -> None:
        self.s3.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=json.dumps(body).encode("utf-8"),
            ContentType="application/json",
        )

    def put_raw(
        self,
        league_id: int,
        season: int,
        endpoint: str,
        dt: date,
        run_id: str,
        part: int,
        body: dict[str, Any],
    ) -> str:
        ep = normalize_endpoint(endpoint)
        key = (
            f"raw/source=api_football/league={league_id}/season={season}/"
            f"endpoint={ep}/dt={dt.isoformat()}/run_id={run_id}/part-{part:05d}.json"
        )
        self.s3.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=json.dumps(body).encode("utf-8"),
            ContentType="application/json",
        )
        return key


# ── GCSWriter ────────────────────────────────────────────────────────────────


class GCSWriter(StorageWriter):
    def __init__(self, bucket: str, project: str | None = None) -> None:
        try:
            from google.cloud import storage as gcs_storage
        except ImportError as exc:
            raise ImportError(
                "google-cloud-storage is required for GCS backend. "
                "Install it with: pip install google-cloud-storage"
            ) from exc

        client = gcs_storage.Client(project=project)
        self._bucket = client.bucket(bucket)

    def marker_exists(self, key: str) -> bool:
        return self._bucket.blob(key).exists()

    def put_marker(self, key: str, body: dict[str, Any]) -> None:
        blob = self._bucket.blob(key)
        blob.upload_from_string(json.dumps(body), content_type="application/json")

    def put_raw(
        self,
        league_id: int,
        season: int,
        endpoint: str,
        dt: date,
        run_id: str,
        part: int,
        body: dict[str, Any],
    ) -> str:
        ep = normalize_endpoint(endpoint)
        key = (
            f"raw/source=api_football/league={league_id}/season={season}/"
            f"endpoint={ep}/dt={dt.isoformat()}/run_id={run_id}/part-{part:05d}.json"
        )
        blob = self._bucket.blob(key)
        blob.upload_from_string(json.dumps(body), content_type="application/json")
        return key


# ── Factory ──────────────────────────────────────────────────────────────────


def create_writer(backend: str, **kwargs: Any) -> StorageWriter:
    if backend == "local":
        return LocalFileWriter(root=kwargs.get("local_root", "data_lake"))
    if backend == "s3":
        bucket = kwargs.get("s3_bucket")
        region = kwargs.get("aws_region")
        if not bucket:
            raise ValueError("s3_bucket is required when storage_backend='s3'")
        if not region:
            raise ValueError("aws_region is required when storage_backend='s3'")
        return S3Writer(bucket=bucket, region=region)
    if backend == "gcs":
        bucket = kwargs.get("gcs_bucket")
        if not bucket:
            raise ValueError("gcs_bucket is required when storage_backend='gcs'")
        return GCSWriter(bucket=bucket, project=kwargs.get("gcs_project"))
    raise ValueError(f"Unknown storage backend: {backend!r}. Must be 'local', 's3', or 'gcs'.")


def generate_run_id() -> str:
    return datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
