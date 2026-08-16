from datetime import datetime, timedelta, timezone
from typing import Any

from app.clients.base import ExternalAPIError, ResilientAsyncClient
from app.core.config import settings


class TossClient(ResilientAsyncClient):
    """Read-only client using only endpoints in the official Toss Securities OpenAPI spec."""

    provider = "toss"

    def __init__(self, client_id: str, client_secret: str):
        super().__init__(
            timeout=settings.external_api_timeout_seconds,
            max_retries=settings.external_api_max_retries,
        )
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = settings.toss_base_url.rstrip("/")
        self._access_token: str | None = None
        self._expires_at: datetime | None = None

    async def _token(self, force: bool = False) -> str:
        now = datetime.now(timezone.utc)
        if not force and self._access_token and self._expires_at and now < self._expires_at:
            return self._access_token
        response = await self.request(
            "POST",
            f"{self.base_url}/oauth2/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
        )
        payload = response.json()
        self._access_token = payload["access_token"]
        expires_in = int(payload.get("expires_in", 3600))
        self._expires_at = now + timedelta(seconds=max(expires_in - 60, 30))
        return self._access_token

    async def _get(self, path: str, *, account_seq: int | None = None, params=None):
        for token_attempt in range(2):
            token = await self._token(force=token_attempt == 1)
            headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
            if account_seq is not None:
                headers["X-Tossinvest-Account"] = str(account_seq)
            try:
                response = await self.request(
                    "GET", f"{self.base_url}{path}", headers=headers, params=params
                )
                return response.json().get("result")
            except ExternalAPIError as exc:
                if exc.status_code == 401 and token_attempt == 0:
                    continue
                raise
        raise ExternalAPIError(self.provider, 401, "Token refresh failed")

    async def accounts(self) -> list[dict[str, Any]]:
        result = await self._get("/api/v1/accounts")
        return result if isinstance(result, list) else []

    async def holdings(self, account_seq: int) -> dict[str, Any]:
        result = await self._get("/api/v1/holdings", account_seq=account_seq)
        return result if isinstance(result, dict) else {"items": []}

    async def usd_krw(self) -> dict[str, Any]:
        result = await self._get(
            "/api/v1/exchange-rate",
            params={"baseCurrency": "USD", "quoteCurrency": "KRW"},
        )
        if not isinstance(result, dict):
            raise ExternalAPIError(self.provider, None, "Malformed exchange-rate response")
        return result
