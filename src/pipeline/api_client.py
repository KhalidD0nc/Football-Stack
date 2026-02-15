from __future__ import annotations

import threading
import time
from typing import Any

import requests
from requests import RequestException
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


class ApiError(RuntimeError):
    pass


class SimpleRateLimiter:
    def __init__(self, max_per_second: float = 5.0) -> None:
        self._interval = 1.0 / max_per_second
        self._lock = threading.Lock()
        self._last_call = 0.0

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            sleep_for = self._interval - (now - self._last_call)
            if sleep_for > 0:
                time.sleep(sleep_for)
            self._last_call = time.monotonic()


class ApiFootballClient:
    def __init__(self, base_url: str, api_key: str, rate_limit_per_sec: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.rate_limiter = SimpleRateLimiter(rate_limit_per_sec)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "x-apisports-key": api_key,
                "Accept": "application/json",
            }
        )

    @retry(
        retry=retry_if_exception_type(ApiError),
        wait=wait_exponential(multiplier=1, min=1, max=32),
        stop=stop_after_attempt(5),
        reraise=True,
    )
    def get(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        self.rate_limiter.wait()

        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=30)
        except RequestException as err:
            raise ApiError(f"Network error for {endpoint}: {err}") from err

        if response.status_code == 429 or response.status_code >= 500:
            raise ApiError(f"Transient API error {response.status_code} for {endpoint}")

        if response.status_code >= 400:
            raise RuntimeError(f"Non-retryable API error {response.status_code}: {response.text[:200]}")

        try:
            payload = response.json()
        except ValueError as err:
            raise RuntimeError(f"Invalid JSON response for {endpoint}") from err

        if not isinstance(payload, dict):
            raise RuntimeError("Unexpected API payload format")

        errors = payload.get("errors")
        if errors:
            raise RuntimeError(f"API payload reported errors for {endpoint}: {errors}")

        return payload
