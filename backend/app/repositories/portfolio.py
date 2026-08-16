from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AllocationTarget,
    AssetSnapshot,
    Debt,
    FinancialAccount,
    FinancialGoal,
    InvestmentAccount,
    InvestmentPosition,
    ManualAsset,
    SavingsProduct,
    SyncRun,
)


class SqlPortfolioRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def accounts(self) -> list[dict[str, Any]]:
        rows = (await self.session.execute(select(FinancialAccount).order_by(FinancialAccount.name))).scalars()
        return [
            {
                "id": str(row.id), "name": row.name, "institution": row.institution,
                "account_type": row.account_type, "currency": row.currency,
                "source_type": row.source_type, "is_active": row.is_active,
                "include_in_net_worth": row.include_in_net_worth,
            }
            for row in rows
        ]

    async def manual_assets(self) -> list[dict[str, Any]]:
        query = (
            select(ManualAsset, FinancialAccount)
            .outerjoin(FinancialAccount, ManualAsset.account_id == FinancialAccount.id)
            .where(ManualAsset.include_in_net_worth.is_(True))
            .where((FinancialAccount.id.is_(None)) | (FinancialAccount.is_active.is_(True)))
        )
        rows = (await self.session.execute(query)).all()
        return [
            {
                "id": str(asset.id), "name": asset.name,
                "account": account.name if account else "미지정",
                "institution": account.institution if account else "",
                "account_source": account.source_type if account else None,
                "asset_type": asset.asset_type, "asset_class": asset.asset_class,
                "amount_krw": asset.amount_krw, "currency": asset.currency,
                "liquidity": asset.liquidity or "보통",
                "valued_at": asset.valued_at.isoformat() if asset.valued_at else None,
            }
            for asset, account in rows
        ]

    async def savings(self) -> list[dict[str, Any]]:
        query = (
            select(SavingsProduct, FinancialAccount)
            .outerjoin(FinancialAccount, SavingsProduct.account_id == FinancialAccount.id)
            .where(SavingsProduct.status == "ACTIVE", SavingsProduct.include_in_net_worth.is_(True))
            .where((FinancialAccount.id.is_(None)) | (FinancialAccount.is_active.is_(True)))
        )
        rows = (await self.session.execute(query)).all()
        return [
            {
                "id": str(item.id), "name": item.name,
                "institution": item.institution or (account.institution if account else ""),
                "product_type": item.product_type, "current_balance": item.current_balance,
                "initial_deposit": item.initial_deposit,
                "monthly_contribution": item.monthly_contribution,
                "base_rate": item.base_rate, "bonus_rate": item.bonus_rate,
                "interest_method": item.interest_method, "tax_type": item.tax_type,
                "opened_at": item.opened_at, "maturity_at": item.maturity_at,
            }
            for item, account in rows
        ]

    async def debts(self) -> list[dict[str, Any]]:
        rows = (
            await self.session.execute(
                select(Debt).where(Debt.status == "ACTIVE", Debt.include_in_net_worth.is_(True))
            )
        ).scalars()
        return [
            {
                "id": str(item.id), "name": item.name, "institution": item.institution,
                "debt_type": item.debt_type, "original_balance": item.original_balance,
                "current_balance": item.current_balance, "annual_rate": item.annual_rate,
                "monthly_payment": item.monthly_payment, "maturity_at": item.maturity_at,
            }
            for item in rows
        ]

    async def positions(self) -> list[dict[str, Any]]:
        query = select(InvestmentPosition, InvestmentAccount).join(
            InvestmentAccount, InvestmentPosition.account_id == InvestmentAccount.id
        )
        rows = (await self.session.execute(query)).all()
        return [
            {
                "id": str(item.id), "name": item.name, "symbol": item.symbol,
                "account": account.display_name, "market": item.market,
                "security_type": item.security_type, "currency": item.currency,
                "quantity": item.quantity, "average_price": item.average_price,
                "current_price": item.current_price, "cost_basis": item.cost_basis,
                "market_value_krw": item.market_value_krw,
                "unrealized_pnl_krw": item.unrealized_pnl_krw,
                "return_rate": item.return_rate,
            }
            for item, account in rows
        ]

    async def allocation_targets(self) -> list[dict[str, Any]]:
        rows = (
            await self.session.execute(
                select(AllocationTarget)
                .where(AllocationTarget.is_active.is_(True))
                .order_by(AllocationTarget.priority, AllocationTarget.target_key)
            )
        ).scalars()
        return [
            {
                "asset_class": item.target_key, "target_weight": item.target_weight,
                "minimum_weight": item.minimum_weight, "maximum_weight": item.maximum_weight,
            }
            for item in rows
        ]

    async def goals(self) -> list[dict[str, Any]]:
        rows = (
            await self.session.execute(select(FinancialGoal).where(FinancialGoal.status == "ACTIVE"))
        ).scalars()
        return [
            {
                "id": str(item.id), "name": item.name, "goal_type": item.goal_type,
                "target_amount": item.target_amount, "starting_amount": item.starting_amount,
                "target_date": item.target_date,
            }
            for item in rows
        ]

    async def history(self, limit: int | None = None) -> list[dict[str, Any]]:
        query = select(AssetSnapshot).order_by(AssetSnapshot.snapshot_date.desc())
        if limit:
            query = query.limit(limit)
        rows = list((await self.session.execute(query)).scalars())
        return [
            {
                "date": item.snapshot_date.isoformat(), "net_worth": item.net_worth,
                "total_assets": item.total_assets, "total_debts": item.total_debts,
            }
            for item in reversed(rows)
        ]

    async def last_sync(self, provider: str) -> datetime | None:
        return (
            await self.session.execute(
                select(SyncRun.completed_at)
                .where(SyncRun.provider == provider, SyncRun.status.in_(["SUCCESS", "PARTIAL"]))
                .order_by(SyncRun.completed_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()


class DemoPortfolioRepository:
    """Deterministic demo data for first run and frontend evaluation."""

    async def accounts(self) -> list[dict[str, Any]]:
        return [
            {"id": "acc-1", "name": "생활비 통장", "institution": "토스뱅크", "account_type": "입출금", "currency": "KRW", "source_type": "NOTION", "is_active": True, "include_in_net_worth": True},
            {"id": "acc-2", "name": "자산관리 계좌", "institution": "미래은행", "account_type": "예적금", "currency": "KRW", "source_type": "NOTION", "is_active": True, "include_in_net_worth": True},
            {"id": "acc-3", "name": "투자 계좌", "institution": "토스증권", "account_type": "증권", "currency": "KRW", "source_type": "TOSS", "is_active": True, "include_in_net_worth": True},
        ]

    async def manual_assets(self) -> list[dict[str, Any]]:
        return [
            {"id": "asset-1", "name": "생활비 잔액", "account": "생활비 통장", "institution": "토스뱅크", "account_source": "NOTION", "asset_type": "입출금계좌", "asset_class": "현금", "amount_krw": Decimal("7320000"), "currency": "KRW", "liquidity": "높음", "valued_at": "2026-08-16"},
            {"id": "asset-2", "name": "비상 현금", "account": "현금", "institution": "직접 보관", "account_source": None, "asset_type": "현금", "asset_class": "현금", "amount_krw": Decimal("2500000"), "currency": "KRW", "liquidity": "높음", "valued_at": "2026-08-16"},
            {"id": "asset-3", "name": "주거 보증금", "account": "주거", "institution": "임대인", "account_source": "NOTION", "asset_type": "월세보증금", "asset_class": "보증금", "amount_krw": Decimal("12000000"), "currency": "KRW", "liquidity": "낮음", "valued_at": "2026-08-01"},
            {"id": "asset-4", "name": "KRX 금현물", "account": "금 계좌", "institution": "한국거래소", "account_source": "NOTION", "asset_type": "금현물", "asset_class": "금", "amount_krw": Decimal("2650000"), "currency": "KRW", "liquidity": "보통", "valued_at": "2026-08-16"},
            {"id": "asset-5", "name": "퇴직연금 잔액", "account": "퇴직연금", "institution": "국민은행", "account_source": "NOTION", "asset_type": "기타금융자산", "asset_class": "기타자산", "amount_krw": Decimal("1800000"), "currency": "KRW", "liquidity": "낮음", "valued_at": "2026-08-01"},
        ]

    async def savings(self) -> list[dict[str, Any]]:
        return [
            {"id": "sav-1", "name": "차곡차곡 정기적금", "institution": "카카오뱅크", "product_type": "정액적립식 적금", "current_balance": Decimal("8300000"), "initial_deposit": Decimal("0"), "monthly_contribution": Decimal("500000"), "base_rate": Decimal("4.2"), "bonus_rate": Decimal("0"), "interest_method": "SIMPLE", "tax_type": "GENERAL", "opened_at": date(2025, 11, 4), "maturity_at": date(2026, 11, 4)},
            {"id": "sav-2", "name": "주택청약종합저축", "institution": "우리은행", "product_type": "청약", "current_balance": Decimal("6160000"), "initial_deposit": Decimal("0"), "monthly_contribution": Decimal("100000"), "base_rate": Decimal("3.1"), "bonus_rate": Decimal("0"), "interest_method": "SIMPLE", "tax_type": "GENERAL", "opened_at": date(2022, 3, 18), "maturity_at": date(2032, 3, 18)},
            {"id": "sav-3", "name": "비상금 정기예금", "institution": "신한은행", "product_type": "예금", "current_balance": Decimal("4000000"), "initial_deposit": Decimal("4000000"), "monthly_contribution": Decimal("0"), "base_rate": Decimal("3.55"), "bonus_rate": Decimal("0"), "interest_method": "SIMPLE", "tax_type": "GENERAL", "opened_at": date(2026, 2, 10), "maturity_at": date(2027, 2, 10)},
        ]

    async def debts(self) -> list[dict[str, Any]]:
        return [
            {"id": "debt-1", "name": "학자금 상환", "institution": "한국장학재단", "debt_type": "학자금대출", "original_balance": Decimal("15000000"), "current_balance": Decimal("9200000"), "annual_rate": Decimal("1.7"), "monthly_payment": Decimal("280000"), "maturity_at": date(2029, 12, 25)},
            {"id": "debt-2", "name": "생활 안정 대출", "institution": "국민은행", "debt_type": "신용대출", "original_balance": Decimal("4000000"), "current_balance": Decimal("2600000"), "annual_rate": Decimal("4.9"), "monthly_payment": Decimal("210000"), "maturity_at": date(2027, 8, 30)},
        ]

    async def positions(self) -> list[dict[str, Any]]:
        values = [
            ("pos-1", "KODEX 미국S&P500TR", "379800", "KRX", "ETF", "KRW", "420", "15920", "18470", "6686400", "7757400", "1071000", "16.02"),
            ("pos-2", "TIGER 미국나스닥100", "133690", "KRX", "ETF", "KRW", "310", "21100", "24030", "6541000", "7449300", "908300", "13.89"),
            ("pos-3", "삼성전자", "005930", "KRX", "개별주식", "KRW", "72", "68100", "75800", "4903200", "5457600", "554400", "11.31"),
            ("pos-4", "Apple", "AAPL", "NASDAQ", "개별주식", "USD", "14", "201.24", "217.38", "3806000", "4371440", "565440", "14.86"),
        ]
        return [
            {"id": item[0], "name": item[1], "symbol": item[2], "account": "토스증권 01", "market": item[3], "security_type": item[4], "currency": item[5], "quantity": Decimal(item[6]), "average_price": Decimal(item[7]), "current_price": Decimal(item[8]), "cost_basis": Decimal(item[9]), "market_value_krw": Decimal(item[10]), "unrealized_pnl_krw": Decimal(item[11]), "return_rate": Decimal(item[12])}
            for item in values
        ]

    async def allocation_targets(self) -> list[dict[str, Any]]:
        values = [("현금", 15, 10, 20), ("예적금", 25, 20, 30), ("ETF", 30, 27, 34), ("개별주식", 10, 7, 13), ("금", 5, 3, 7), ("보증금", 12, 10, 16), ("기타자산", 3, 0, 5)]
        return [{"asset_class": name, "target_weight": Decimal(target), "minimum_weight": Decimal(low), "maximum_weight": Decimal(high)} for name, target, low, high in values]

    async def goals(self) -> list[dict[str, Any]]:
        return [
            {"id": "goal-1", "name": "비상금 800만원", "goal_type": "현금", "target_amount": Decimal("8000000"), "starting_amount": Decimal("1000000"), "target_date": date(2026, 12, 31)},
            {"id": "goal-2", "name": "순자산 8천만원", "goal_type": "순자산", "target_amount": Decimal("80000000"), "starting_amount": Decimal("46000000"), "target_date": date(2027, 12, 31)},
            {"id": "goal-3", "name": "투자자산 4천만원", "goal_type": "투자", "target_amount": Decimal("40000000"), "starting_amount": Decimal("15000000"), "target_date": date(2028, 6, 30)},
        ]

    async def history(self, limit: int | None = None) -> list[dict[str, Any]]:
        net_values = [Decimal(str(v)) * 1_000_000 for v in [46.2, 46.8, 47.9, 48.6, 49.4, 50.7, 51.5, 52.9, 54.1, 54.8, 55.54714, 57.96574]]
        rows = []
        for index, net in enumerate(net_values):
            month = 9 + index
            year = 2025 + (month - 1) // 12
            month = ((month - 1) % 12) + 1
            debt = Decimal("13100000") - Decimal(index * 118182)
            rows.append({"date": date(year, month, 16).isoformat(), "net_worth": net, "total_assets": net + debt, "total_debts": debt})
        return rows[-limit:] if limit else rows

    async def last_sync(self, provider: str) -> datetime | None:
        minute = 17 if provider == "NOTION" else 19
        return datetime(2026, 8, 16, 10, minute, tzinfo=timezone.utc)
