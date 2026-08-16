from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.portfolio import router as portfolio_router
from app.api.routes.webhooks import router as webhook_router
from app.core.config import settings
from app.core.logging import configure_logging


configure_logging()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Read-only personal asset portfolio API",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Request-ID"],
)
app.include_router(portfolio_router)
app.include_router(webhook_router)


@app.get("/health")
async def health():
    return {"status": "ok", "demo_mode": settings.demo_mode}
