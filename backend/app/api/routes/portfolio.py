from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_session
from app.models import FinancialAccount
from app.repositories.portfolio import DemoPortfolioRepository, SqlPortfolioRepository
from app.services.portfolio import PortfolioService
from app.services.snapshots import SnapshotService
from app.services.sync import NotionSyncService, TossSyncService


router = APIRouter(prefix="/api")
Session = Annotated[AsyncSession, Depends(get_session)]


def service_for(session: AsyncSession) -> PortfolioService:
    repository = DemoPortfolioRepository() if settings.demo_mode else SqlPortfolioRepository(session)
    return PortfolioService(repository)


@router.get("/dashboard/summary")
async def dashboard_summary(session: Session):
    return await service_for(session).summary()


@router.get("/dashboard/allocation")
@router.get("/allocation")
async def dashboard_allocation(session: Session):
    return await service_for(session).allocation()


@router.get("/dashboard/net-worth-history")
@router.get("/history/net-worth")
async def net_worth_history(
    session: Session,
    range: str = Query(default="1y", pattern="^(1m|3m|6m|1y|all)$"),
):
    limit = {"1m": 31, "3m": 92, "6m": 183, "1y": 366, "all": None}[range]
    repository = DemoPortfolioRepository() if settings.demo_mode else SqlPortfolioRepository(session)
    return await repository.history(limit=limit)


@router.get("/accounts")
async def accounts(session: Session):
    repository = DemoPortfolioRepository() if settings.demo_mode else SqlPortfolioRepository(session)
    return await repository.accounts()


@router.get("/accounts/{account_id}")
async def account_detail(account_id: str, session: Session):
    if settings.demo_mode:
        items = await DemoPortfolioRepository().accounts()
        account = next((item for item in items if item["id"] == account_id), None)
    else:
        account = (await session.execute(select(FinancialAccount).where(FinancialAccount.id == account_id))).scalar_one_or_none()
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.get("/assets")
async def assets(session: Session):
    return await service_for(session).assets()


@router.get("/savings")
async def savings(session: Session):
    return await service_for(session).savings()


@router.get("/savings/{savings_id}")
async def savings_detail(savings_id: str, session: Session):
    items = await service_for(session).savings()
    item = next((row for row in items if row["id"] == savings_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="Savings product not found")
    return item


@router.get("/debts")
async def debts(session: Session):
    return await service_for(session).debts()


@router.get("/investments")
async def investments(session: Session):
    positions = await service_for(session).positions()
    market_value = sum((item["market_value_krw"] for item in positions), 0)
    cost_basis = sum((item["cost_basis"] for item in positions), 0)
    return {
        "market_value": market_value,
        "cost_basis": cost_basis,
        "unrealized_pnl": market_value - cost_basis,
        "positions": positions,
    }


@router.get("/investments/accounts")
async def investment_accounts(session: Session):
    repository = DemoPortfolioRepository() if settings.demo_mode else SqlPortfolioRepository(session)
    return [item for item in await repository.accounts() if item["source_type"] == "TOSS"]


@router.get("/investments/positions")
async def investment_positions(session: Session):
    return await service_for(session).positions()


@router.get("/goals")
async def goals(session: Session):
    return await service_for(session).goals()


@router.get("/sync/status")
async def sync_status(session: Session):
    if settings.demo_mode:
        repository = DemoPortfolioRepository()
        notion = await repository.last_sync("NOTION")
        toss = await repository.last_sync("TOSS")
        return {
            "notion": {"state": "connected", "last_sync": notion, "message": "6개 Data Source 연결됨"},
            "toss": {"state": "connected", "last_sync": toss, "message": "읽기 전용 · 1개 계좌"},
            "database": {"state": "connected", "last_sync": notion, "message": "데모 데이터 모드"},
        }
    try:
        await session.execute(text("SELECT 1"))
        database_state = "connected"
    except Exception:
        database_state = "disconnected"
    repository = SqlPortfolioRepository(session)
    notion = await repository.last_sync("NOTION")
    toss = await repository.last_sync("TOSS")
    return {
        "notion": {"state": "connected" if settings.notion_api_key else "disconnected", "last_sync": notion, "message": "6개 Data Source" if settings.notion_api_key else "환경변수 설정 필요"},
        "toss": {"state": "connected" if settings.toss_client_id else "disconnected", "last_sync": toss, "message": "읽기 전용" if settings.toss_client_id else "환경변수 설정 필요"},
        "database": {"state": database_state, "last_sync": None, "message": "PostgreSQL 정상" if database_state == "connected" else "연결 확인 필요"},
    }


@router.post("/sync/notion")
async def sync_notion(session: Session):
    if settings.demo_mode:
        return {"status": "success", "provider": "notion", "mode": "demo"}
    try:
        return await NotionSyncService(session).run()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/sync/toss")
async def sync_toss(session: Session):
    if settings.demo_mode:
        return {"status": "success", "provider": "toss", "mode": "demo"}
    try:
        return await TossSyncService(session).run()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/snapshots")
async def create_snapshot(session: Session):
    if settings.demo_mode:
        summary = await service_for(session).summary()
        return {"status": "success", "mode": "demo", "net_worth": summary["net_worth"]}
    service = service_for(session)
    return await SnapshotService(session, service).create()
