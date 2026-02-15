from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from typing import Any

import boto3
from botocore.exceptions import ClientError


class S3Writer:
    def __init__(self, bucket: str, region: str) -> None:
        self.bucket = bucket
        self.s3 = boto3.client("s3", region_name=region)

    @staticmethod
    def _normalize_endpoint(endpoint: str) -> str:
        return endpoint.strip("/").replace("/", "_")

    def idempotency_key_from_parts(self, *parts: object) -> str:
        raw = "|".join(str(part) for part in parts).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def idempotency_key(self, endpoint: str, fixture_id: int, season: int, dt: date) -> str:
        return self.idempotency_key_from_parts(endpoint, fixture_id, season, dt.isoformat())

    def marker_key(self, league_id: int, season: int, endpoint: str, dt: date, idem_key: str) -> str:
        ep = self._normalize_endpoint(endpoint)
        return (
            f"state/source=api_football/league={league_id}/season={season}/"
            f"endpoint={ep}/dt={dt.isoformat()}/idempotency_key={idem_key}.json"
        )

    def marker_exists(self, key: str) -> bool:
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
        ep = self._normalize_endpoint(endpoint)
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


def generate_run_id() -> str:
    return datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
