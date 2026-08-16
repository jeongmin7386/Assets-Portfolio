import hashlib
import hmac
import json

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.sync import NotionSyncService


router = APIRouter(prefix="/api/webhooks")


async def _full_sync() -> None:
    async with SessionLocal() as session:
        await NotionSyncService(session).run()


@router.post("/notion")
async def notion_webhook(request: Request, background_tasks: BackgroundTasks):
    raw_body = await request.body()
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON") from exc

    if "verification_token" in payload:
        return {"status": "verification_received"}

    verification_token = settings.notion_webhook_verification_token
    if not verification_token:
        raise HTTPException(status_code=503, detail="Webhook verification token not configured")
    signature = request.headers.get("X-Notion-Signature", "")
    expected = "sha256=" + hmac.new(
        verification_token.encode(), raw_body, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # Webhooks are change signals only. Fetch authoritative values again through the Notion API.
    background_tasks.add_task(_full_sync)
    return {"status": "accepted", "event_id": payload.get("id")}
