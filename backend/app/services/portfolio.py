from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Protocol

from app.services.calculations import (
    calculate_allocation,
    calculate_portfolio,
    calculate_savings_projection,
    goal_current_value,
    money,
    rate,
)


class PortfolioRepository(Protocol):
    async def accounts(self) -> list[dict[str, Any]]: ...
    async def manual_assets(self) -> list[dict[str, Any]]: ...
    async def savings(self) -> list[dict[str, Any]]: ...
    async def debts(self) -> list[dict[str, Any]]: ...
    async def positions(self) -> list[dict[str, Any]]: ...
    async def allocation_targets(self) -> list[dict[str, Any]]: ...
    async def goals(self) -> list[dict[str, Any]]: ...
    async def history(self, limit: int | None = None) -> list[dict[str, Any]]: ...
    async def last_sync(self, provider: str) -> datetime | None: ...


class PortfolioService:
    def __init__(self, repository: PortfolioRepository, today: date | None = None):
        self.repository = repository
        self.today = today or date.today()

    async def _portfolio(self) -> dict[str, Any]:
        manual_assets, savings, positions, debts = await self._source_data()
        return calculate_portfolio(manual_assets, savings, positions, debts)

    async def _source_data(self):
        manual_assets = await self.repository.manual_assets()
        savings = await self.repository.savings()
        positions = await self.repository.positions()
        debts = await self.repository.debts()
        return manual_assets, savings, positions, debts

    async def summary(self) -> dict[str, Any]:
        portfolio = await self._portfolio()
        history = await self.repository.history(limit=2)
        previous = money(history[-2]["net_worth"]) if len(history) > 1 else portfolio["net_worth"]
        change = money(portfolio["net_worth"] - previous)
        change_rate = rate(change / previous * Decimal("100")) if previous else Decimal("0")
        notion_sync = await self.repository.last_sync("NOTION")
        toss_sync = await self.repository.last_sync("TOSS")
        classes = portfolio["class_values"]
        return {
            "as_of": datetime.now(timezone.utc),
            "net_worth": portfolio["net_worth"],
            "total_assets": portfolio["total_assets"],
            "total_debts": portfolio["total_debts"],
            "cash_value": classes["현금"],
            "savings_value": classes["예적금"],
            "investment_value": portfolio["investment_value"],
            "gold_value": classes["금"],
            "deposit_value": classes["보증금"],
            "other_assets_value": classes["기타자산"],
            "net_worth_change": {"amount": change, "rate": change_rate},
            "last_notion_sync": notion_sync,
            "last_toss_sync": toss_sync,
            "warnings": portfolio["warnings"],
        }

    async def allocation(self) -> list[dict[str, Any]]:
        portfolio = await self._portfolio()
        targets = await self.repository.allocation_targets()
        return calculate_allocation(portfolio["class_values"], targets)

    async def assets(self) -> list[dict[str, Any]]:
        return await self.repository.manual_assets()

    async def positions(self) -> list[dict[str, Any]]:
        positions = await self.repository.positions()
        total = sum((money(item["market_value_krw"]) for item in positions), Decimal("0"))
        for item in positions:
            item["portfolio_weight"] = rate(money(item["market_value_krw"]) / total * Decimal("100")) if total else Decimal("0")
        return positions

    async def savings(self) -> list[dict[str, Any]]:
        return [calculate_savings_projection(item, self.today) for item in await self.repository.savings()]

    async def debts(self) -> list[dict[str, Any]]:
        items = await self.repository.debts()
        for item in items:
            original = money(item["original_balance"])
            current = money(item["current_balance"])
            item["repayment_progress"] = rate((original - current) / original * Decimal("100")) if original else Decimal("0")
        return items

    async def goals(self) -> list[dict[str, Any]]:
        portfolio = await self._portfolio()
        result = []
        for item in await self.repository.goals():
            current = goal_current_value(item["goal_type"], portfolio)
            target = money(item["target_amount"])
            progress = rate(current / target * Decimal("100")) if target else Decimal("0")
            target_date = item.get("target_date")
            result.append({
                **item,
                "current_value": current,
                "progress": progress,
                "days_remaining": max((target_date - self.today).days, 0) if target_date else 0,
            })
        return result
