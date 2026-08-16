from typing import Any, AsyncIterator

from app.clients.base import ResilientAsyncClient
from app.core.config import settings


class NotionClient(ResilientAsyncClient):
    provider = "notion"
    base_url = "https://api.notion.com/v1"

    def __init__(self, api_key: str):
        super().__init__(
            timeout=settings.external_api_timeout_seconds,
            max_retries=settings.external_api_max_retries,
        )
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Notion-Version": settings.notion_api_version,
            "Content-Type": "application/json",
        }

    async def query_data_source(self, data_source_id: str) -> AsyncIterator[dict[str, Any]]:
        cursor: str | None = None
        while True:
            body: dict[str, Any] = {"page_size": 100}
            if cursor:
                body["start_cursor"] = cursor
            response = await self.request(
                "POST",
                f"{self.base_url}/data_sources/{data_source_id}/query",
                headers=self.headers,
                json=body,
            )
            payload = response.json()
            for item in payload.get("results", []):
                if item.get("object") == "page":
                    yield item
            if not payload.get("has_more"):
                break
            cursor = payload.get("next_cursor")
            if not cursor:
                break

    async def retrieve_page(self, page_id: str) -> dict[str, Any]:
        response = await self.request(
            "GET", f"{self.base_url}/pages/{page_id}", headers=self.headers
        )
        return response.json()
