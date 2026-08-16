import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.notion_client import NotionClient
from app.clients.toss_client import TossClient
from app.core.config import settings
from app.models import (
    AllocationTarget,
    Debt,
    ExchangeRate,
    FinancialAccount,
    FinancialGoal,
    InvestmentAccount,
    InvestmentPosition,
    ManualAsset,
    SavingsProduct,
    SyncRun,
)
from app.services.notion.parser import parse_page
from app.services.notion.property_maps import PROPERTY_MAPS
from app.services.toss.mapper import map_holding


logger = logging.getLogger(__name__)


NOTION_MODELS = {
    "accounts": FinancialAccount,
    "assets": ManualAsset,
    "savings": SavingsProduct,
    "debts": Debt,
    "goals": FinancialGoal,
    "allocation_targets": AllocationTarget,
}


def classify_asset(asset_type: str | None, explicit: str | None) -> str:
    if explicit:
        return explicit
    normalized = (asset_type or "").replace(" ", "").lower()
    mapping = {
        "입출금계좌": "현금", "현금": "현금", "보증금": "보증금",
        "월세보증금": "보증금", "금": "금", "금현물": "금", "귀금속": "금",
        "기타금융자산": "기타자산",
    }
    return mapping.get(normalized, "기타자산")


def _defaults(dataset: str, payload: dict[str, Any]) -> dict[str, Any]:
    if dataset == "accounts":
        payload.update({
            "name": payload.get("name") or "이름 없는 계좌",
            "institution": payload.get("institution") or "",
            "account_type": payload.get("account_type") or "OTHER",
            "currency": payload.get("currency") or "KRW",
            "source_type": payload.get("source_type") or "NOTION",
            "is_active": payload.get("is_active") if payload.get("is_active") is not None else True,
            "include_in_net_worth": payload.get("include_in_net_worth") if payload.get("include_in_net_worth") is not None else True,
        })
    elif dataset == "assets":
        payload.update({
            "name": payload.get("name") or "이름 없는 자산",
            "asset_type": payload.get("asset_type") or "OTHER",
            "asset_class": classify_asset(payload.get("asset_type"), payload.get("asset_class")),
            "amount_native": payload.get("amount_native") or Decimal("0"),
            "currency": payload.get("currency") or "KRW",
            "include_in_net_worth": payload.get("include_in_net_worth") if payload.get("include_in_net_worth") is not None else True,
        })
        payload["amount_krw"] = payload["amount_native"] if payload["currency"] == "KRW" else Decimal("0")
    elif dataset == "savings":
        for key in ("current_balance", "initial_deposit", "monthly_contribution", "base_rate", "bonus_rate"):
            payload[key] = payload.get(key) or Decimal("0")
        payload.update({"name": payload.get("name") or "이름 없는 예적금", "institution": "", "product_type": payload.get("product_type") or "OTHER", "status": payload.get("status") or "ACTIVE", "include_in_net_worth": payload.get("include_in_net_worth") if payload.get("include_in_net_worth") is not None else True})
    elif dataset == "debts":
        for key in ("original_balance", "current_balance", "annual_rate", "monthly_payment"):
            payload[key] = payload.get(key) or Decimal("0")
        payload.update({"name": payload.get("name") or "이름 없는 부채", "institution": payload.get("institution") or "", "debt_type": payload.get("debt_type") or "OTHER", "status": payload.get("status") or "ACTIVE", "include_in_net_worth": payload.get("include_in_net_worth") if payload.get("include_in_net_worth") is not None else True})
    elif dataset == "goals":
        payload.update({"name": payload.get("name") or "이름 없는 목표", "goal_type": payload.get("goal_type") or "현금", "target_amount": payload.get("target_amount") or Decimal("0"), "starting_amount": payload.get("starting_amount") or Decimal("0"), "status": payload.get("status") or "ACTIVE"})
    elif dataset == "allocation_targets":
        payload.update({"name": payload.get("name") or payload.get("target_key") or "자산배분", "classification_type": payload.get("classification_type") or "ASSET_CLASS", "target_key": payload.get("target_key") or "기타자산", "target_weight": payload.get("target_weight") or Decimal("0"), "priority": int(payload.get("priority") or 0), "is_active": payload.get("is_active") if payload.get("is_active") is not None else True})
    return payload


class NotionSyncService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def run(self) -> dict[str, Any]:
        if not settings.notion_api_key or not all(settings.notion_data_sources.values()):
            raise ValueError("Notion API key와 6개 Data Source ID를 모두 설정해야 합니다.")
        run = SyncRun(provider="NOTION", status="RUNNING", started_at=datetime.now(timezone.utc))
        self.session.add(run)
        await self.session.flush()
        result: dict[str, Any] = {"status": "success"}
        client = NotionClient(settings.notion_api_key)
        try:
            for dataset in ("accounts", "assets", "savings", "debts", "goals", "allocation_targets"):
                counts = await self._sync_dataset(client, dataset, settings.notion_data_sources[dataset])
                result[dataset] = counts
                run.created_count += counts["created"]
                run.updated_count += counts["updated"]
                run.skipped_count += counts["skipped"]
            run.status = "SUCCESS"
            run.completed_at = datetime.now(timezone.utc)
            await self.session.commit()
        except Exception as exc:
            await self.session.rollback()
            failed_run = SyncRun(
                provider="NOTION", status="FAILED", started_at=run.started_at,
                completed_at=datetime.now(timezone.utc), error_code=type(exc).__name__,
                error_message=str(exc)[:1000],
            )
            self.session.add(failed_run)
            await self.session.commit()
            logger.exception("Notion sync failed")
            raise
        finally:
            await client.close()
        return result

    async def _sync_dataset(self, client: NotionClient, dataset: str, source_id: str | None):
        if not source_id:
            return {"created": 0, "updated": 0, "skipped": 1}
        model = NOTION_MODELS[dataset]
        created = updated = skipped = 0
        async for page in client.query_data_source(source_id):
            try:
                payload = _defaults(dataset, parse_page(page, PROPERTY_MAPS[dataset]))
                relation_ids = payload.pop("account", []) or []
                if relation_ids and dataset in {"assets", "savings", "debts"}:
                    payload["account_id"] = (
                        await self.session.execute(
                            select(FinancialAccount.id).where(FinancialAccount.notion_page_id == relation_ids[0])
                        )
                    ).scalar_one_or_none()
                existing = (
                    await self.session.execute(
                        select(model.id).where(model.notion_page_id == payload["notion_page_id"])
                    )
                ).scalar_one_or_none()
                valid_columns = {column.name for column in model.__table__.columns}
                payload = {key: value for key, value in payload.items() if key in valid_columns}
                statement = pg_insert(model).values(**payload)
                statement = statement.on_conflict_do_update(
                    index_elements=[model.notion_page_id],
                    set_={key: value for key, value in payload.items() if key != "notion_page_id"},
                )
                await self.session.execute(statement)
                if existing:
                    updated += 1
                else:
                    created += 1
            except (KeyError, TypeError, ValueError):
                skipped += 1
                logger.warning("Skipped invalid Notion record in %s", dataset)
        await self.session.flush()
        return {"created": created, "updated": updated, "skipped": skipped}


class TossSyncService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def run(self) -> dict[str, Any]:
        if not settings.toss_client_id or not settings.toss_client_secret:
            raise ValueError("TOSS_CLIENT_ID와 TOSS_CLIENT_SECRET을 설정해야 합니다.")
        run = SyncRun(provider="TOSS", status="RUNNING", started_at=datetime.now(timezone.utc))
        self.session.add(run)
        await self.session.flush()
        client = TossClient(settings.toss_client_id, settings.toss_client_secret)
        try:
            exchange = await client.usd_krw()
            usd_krw = Decimal(exchange["rate"])
            self.session.add(ExchangeRate(
                base_currency=exchange["baseCurrency"], quote_currency=exchange["quoteCurrency"],
                rate=usd_krw, provider="TOSS",
                quoted_at=datetime.fromisoformat(exchange["validFrom"]),
            ))
            accounts = await client.accounts()
            position_count = 0
            for account in accounts:
                account_seq = int(account["accountSeq"])
                provider_id = str(account_seq)
                financial_id = await self._upsert_financial_account(account)
                investment_id = await self._upsert_investment_account(account, financial_id)
                holdings = await client.holdings(account_seq)
                for item in holdings.get("items", []):
                    mapped = map_holding(item, usd_krw)
                    mapped["account_id"] = investment_id
                    statement = pg_insert(InvestmentPosition).values(**mapped).on_conflict_do_update(
                        constraint="uq_position_account_symbol",
                        set_={key: value for key, value in mapped.items() if key not in {"account_id", "symbol"}},
                    )
                    await self.session.execute(statement)
                    position_count += 1
            run.updated_count = len(accounts) + position_count
            run.status = "SUCCESS"
            run.completed_at = datetime.now(timezone.utc)
            await self.session.commit()
            return {"status": "success", "accounts": len(accounts), "positions": position_count}
        except Exception as exc:
            await self.session.rollback()
            self.session.add(SyncRun(
                provider="TOSS", status="FAILED", started_at=run.started_at,
                completed_at=datetime.now(timezone.utc), error_code=type(exc).__name__,
                error_message=str(exc)[:1000],
            ))
            await self.session.commit()
            logger.exception("Toss sync failed")
            raise
        finally:
            await client.close()

    async def _upsert_financial_account(self, account: dict[str, Any]):
        provider_id = str(account["accountSeq"])
        payload = {
            "provider_account_id": provider_id,
            "name": f"토스증권 {provider_id}",
            "institution": "토스증권",
            "account_type": account["accountType"],
            "currency": "KRW",
            "source_type": "TOSS",
            "is_active": True,
            "include_in_net_worth": True,
        }
        statement = pg_insert(FinancialAccount).values(**payload).on_conflict_do_update(
            index_elements=[FinancialAccount.provider_account_id], set_=payload
        ).returning(FinancialAccount.id)
        return (await self.session.execute(statement)).scalar_one()

    async def _upsert_investment_account(self, account: dict[str, Any], financial_id):
        provider_id = str(account["accountSeq"])
        payload = {
            "financial_account_id": financial_id, "provider": "TOSS",
            "provider_account_id": provider_id, "display_name": f"토스증권 {provider_id}",
            "currency": "KRW", "synced_at": datetime.now(timezone.utc),
        }
        statement = pg_insert(InvestmentAccount).values(**payload).on_conflict_do_update(
            index_elements=[InvestmentAccount.provider_account_id], set_=payload
        ).returning(InvestmentAccount.id)
        return (await self.session.execute(statement)).scalar_one()
