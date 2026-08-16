import asyncio
import random
from typing import Any

import httpx


class ExternalAPIError(RuntimeError):
    def __init__(self, provider: str, status_code: int | None, message: str):
        super().__init__(f"{provider} API request failed: {message}")
        self.provider = provider
        self.status_code = status_code


class ResilientAsyncClient:
    provider = "external"

    def __init__(self, *, timeout: float, max_retries: int):
        self.max_retries = max_retries
        self.client = httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        await self.client.aclose()

    async def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = await self.client.request(method, url, **kwargs)
                if response.status_code == 429 or response.status_code >= 500:
                    if attempt == self.max_retries:
                        response.raise_for_status()
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else (2**attempt) + random.random()
                    await asyncio.sleep(min(delay, 8))
                    continue
                response.raise_for_status()
                return response
            except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
                last_error = exc
                retryable = not isinstance(exc, httpx.HTTPStatusError) or exc.response.status_code >= 500
                if not retryable or attempt == self.max_retries:
                    status = exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else None
                    raise ExternalAPIError(self.provider, status, str(exc)) from exc
                await asyncio.sleep(min((2**attempt) + random.random(), 8))
        raise ExternalAPIError(self.provider, None, str(last_error))
