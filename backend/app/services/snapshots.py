from datetime import date
from typing import Any

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AssetSnapshot, AssetSnapshotItem
from app.services.portfolio import PortfolioService


class SnapshotService:
    def __init__(self, session: AsyncSession, portfolio_service: PortfolioService):
        self.session = session
        self.portfolio_service = portfolio_service

    async def create(self, snapshot_date: date | None = None) -> dict[str, Any]:
        day = snapshot_date or date.today()
        manual, savings, positions, debts = await self.portfolio_service._source_data()
        portfolio = await self.portfolio_service._portfolio()
        classes = portfolio["class_values"]
        payload = {
            "snapshot_date": day,
            "manual_assets_value": portfolio["manual_assets_value"],
            "cash_value": classes["현금"], "savings_value": classes["예적금"],
            "investment_value": portfolio["investment_value"], "gold_value": classes["금"],
            "deposit_value": classes["보증금"], "other_assets_value": classes["기타자산"],
            "total_assets": portfolio["total_assets"], "total_debts": portfolio["total_debts"],
            "net_worth": portfolio["net_worth"],
        }
        statement = pg_insert(AssetSnapshot).values(**payload).on_conflict_do_update(
            index_elements=[AssetSnapshot.snapshot_date], set_=payload
        ).returning(AssetSnapshot.id)
        snapshot_id = (await self.session.execute(statement)).scalar_one()
        await self.session.execute(
            AssetSnapshotItem.__table__.delete().where(AssetSnapshotItem.snapshot_id == snapshot_id)
        )
        items = []
        for item in manual:
            if item.get("account_source") != "TOSS":
                items.append({"source_type": "MANUAL_ASSET", "source_id": item["id"], "asset_class": item["asset_class"], "name": item["name"], "value_krw": item["amount_krw"]})
        items.extend({"source_type": "SAVINGS", "source_id": item["id"], "asset_class": "예적금", "name": item["name"], "value_krw": item["current_balance"]} for item in savings)
        items.extend({"source_type": "INVESTMENT", "source_id": item["id"], "asset_class": item["security_type"] if item["security_type"] in {"ETF", "개별주식"} else "기타자산", "name": item["name"], "value_krw": item["market_value_krw"]} for item in positions)
        if items:
            await self.session.execute(pg_insert(AssetSnapshotItem), [{"snapshot_id": snapshot_id, **item} for item in items])
        await self.session.commit()
        return {"status": "success", "snapshot_date": day, "net_worth": portfolio["net_worth"], "items": len(items)}
