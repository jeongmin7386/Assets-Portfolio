from datetime import date, datetime
from decimal import Decimal
from typing import Any


def _plain_text(items: list[dict[str, Any]] | None) -> str:
    return "".join(item.get("plain_text", "") for item in (items or []))


def property_value(prop: dict[str, Any] | None) -> Any:
    if not prop:
        return None
    kind = prop.get("type")
    value = prop.get(kind) if kind else None
    if kind in {"title", "rich_text"}:
        return _plain_text(value)
    if kind in {"select", "status"}:
        return value.get("name") if value else None
    if kind == "multi_select":
        return [item.get("name") for item in value or []]
    if kind == "number":
        return Decimal(str(value)) if value is not None else None
    if kind == "checkbox":
        return bool(value)
    if kind == "date":
        return date.fromisoformat(value["start"][:10]) if value and value.get("start") else None
    if kind == "relation":
        return [item["id"] for item in value or []]
    if kind in {"url", "email", "phone_number"}:
        return value
    return None


def parse_page(page: dict[str, Any], mapping: dict[str, str]) -> dict[str, Any]:
    properties = page.get("properties", {})
    parsed = {
        field: property_value(properties.get(notion_name))
        for field, notion_name in mapping.items()
    }
    parsed["notion_page_id"] = page["id"]
    parsed["notion_last_edited_time"] = datetime.fromisoformat(
        page["last_edited_time"].replace("Z", "+00:00")
    )
    return parsed
