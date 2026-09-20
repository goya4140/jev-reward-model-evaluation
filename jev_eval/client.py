from __future__ import annotations

import asyncio
import os
import random
import time
from dataclasses import dataclass
from typing import Any

import httpx


API_URL = "https://api.typesafe.ai/v1/systemone"


class JevError(RuntimeError):
    pass


class JevBillingError(JevError):
    """Non-retryable account credit failure that must stop a run immediately."""


@dataclass
class JevResult:
    model: str
    answers: dict[str, Any]
    usage: dict[str, int]
    latency_ms: float


class JevClient:
    def __init__(
        self,
        *,
        model: str = "jev-1.13.0",
        concurrency: int = 24,
        timeout_s: float = 120.0,
        max_attempts: int = 6,
    ) -> None:
        api_key = os.environ.get("TYPESAFE_API_KEY")
        if not api_key:
            raise JevError("TYPESAFE_API_KEY is not set")
        self.model = model
        self.max_attempts = max_attempts
        self._sem = asyncio.Semaphore(concurrency)
        self._http = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=httpx.Timeout(timeout_s),
            limits=httpx.Limits(
                max_connections=concurrency,
                max_keepalive_connections=concurrency,
            ),
        )

    async def close(self) -> None:
        await self._http.aclose()

    async def evaluate(self, state: Any, questions: dict[str, Any]) -> JevResult:
        payload = {"state": state, "model": self.model, "questions": questions}
        async with self._sem:
            for attempt in range(self.max_attempts):
                started = time.perf_counter()
                try:
                    response = await self._http.post(API_URL, json=payload)
                except (httpx.TimeoutException, httpx.NetworkError) as exc:
                    if attempt + 1 == self.max_attempts:
                        raise JevError(f"network error after retries: {exc}") from exc
                    await asyncio.sleep(min(20.0, 0.5 * 2**attempt) + random.random() / 4)
                    continue

                latency_ms = (time.perf_counter() - started) * 1000
                if response.status_code < 400:
                    body = response.json()
                    return JevResult(
                        model=body["model"],
                        answers=body["answers"],
                        usage=body.get("usage", {}),
                        latency_ms=latency_ms,
                    )

                if response.status_code not in {408, 409, 429, 500, 502, 503, 504}:
                    if response.status_code == 402:
                        raise JevBillingError(
                            f"API returned 402: {response.text[:500]}"
                        )
                    raise JevError(
                        f"API returned {response.status_code}: {response.text[:500]}"
                    )
                if attempt + 1 == self.max_attempts:
                    raise JevError(
                        f"API returned {response.status_code} after retries: "
                        f"{response.text[:500]}"
                    )
                retry_after = response.headers.get("retry-after")
                delay = float(retry_after) if retry_after else min(20.0, 0.5 * 2**attempt)
                await asyncio.sleep(delay + random.random() / 4)

        raise AssertionError("unreachable")
