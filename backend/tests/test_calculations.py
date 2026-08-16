from datetime import date
from decimal import Decimal

import pytest

from app.services.calculations import (
    calculate_allocation,
    calculate_portfolio,
    calculate_savings_projection,
    convert_currency,
    goal_current_value,
)


def sources():
    assets = [
        {"name": "cash", "asset_class": "현금", "amount_krw": Decimal("1000"), "account_source": "NOTION"},
        {"name": "gold", "asset_class": "금", "amount_krw": Decimal("500"), "account_source": "NOTION"},
    ]
    savings = [{"current_balance": Decimal("2000")}]
    positions = [{"security_type": "ETF", "market_value_krw": Decimal("3000")}]
    debts = [{"current_balance": Decimal("1200")}]
    return assets, savings, positions, debts


def test_total_assets_and_net_worth_calculation():
    portfolio = calculate_portfolio(*sources())
    assert portfolio["total_assets"] == Decimal("6500.00")
    assert portfolio["total_debts"] == Decimal("1200.00")
    assert portfolio["net_worth"] == Decimal("5300.00")


def test_asset_allocation_excludes_debt_denominator():
    portfolio = calculate_portfolio(*sources())
    result = calculate_allocation(
        portfolio["class_values"],
        [{"asset_class": "ETF", "target_weight": 50, "minimum_weight": 45, "maximum_weight": 55}],
    )
    etf = next(item for item in result if item["asset_class"] == "ETF")
    assert etf["current_weight"] == Decimal("46.15")
    assert etf["status"] == "NORMAL"


def test_allocation_difference_is_percentage_points():
    portfolio = calculate_portfolio(*sources())
    result = calculate_allocation(
        portfolio["class_values"],
        [{"asset_class": "현금", "target_weight": 20, "minimum_weight": 18, "maximum_weight": 22}],
    )
    cash = next(item for item in result if item["asset_class"] == "현금")
    assert cash["weight_difference"] == Decimal("-4.62")
    assert cash["status"] == "UNDERWEIGHT"


def test_goal_progress_uses_computed_portfolio_value():
    portfolio = calculate_portfolio(*sources())
    assert goal_current_value("순자산", portfolio) == Decimal("5300.00")
    assert goal_current_value("투자", portfolio) == Decimal("3000.00")
    assert goal_current_value("현금", portfolio) == Decimal("1000.00")


def test_savings_projection_uses_decimal_and_marks_estimate():
    result = calculate_savings_projection(
        {
            "current_balance": Decimal("1000000"), "monthly_contribution": Decimal("100000"),
            "base_rate": Decimal("3.5"), "bonus_rate": Decimal("0.5"),
            "opened_at": date(2026, 1, 1), "maturity_at": date(2027, 1, 1),
            "tax_type": "GENERAL",
        },
        date(2026, 7, 1),
    )
    assert result["is_estimated"] is True
    assert result["days_remaining"] == 184
    assert result["estimated_maturity_amount"] > Decimal("1600000")


def test_invalid_savings_dates_are_rejected():
    with pytest.raises(ValueError):
        calculate_savings_projection(
            {"opened_at": date(2027, 1, 1), "maturity_at": date(2026, 1, 1)},
            date(2026, 1, 1),
        )


def test_currency_conversion():
    assert convert_currency(Decimal("1000"), "USD", Decimal("1350")) == Decimal("1350000.00")


def test_unsupported_currency_rejected():
    with pytest.raises(ValueError):
        convert_currency(Decimal("1000"), "EUR", None)


def test_toss_manual_asset_is_excluded_and_warned():
    assets, savings, positions, debts = sources()
    assets.append({"name": "duplicate", "asset_class": "기타자산", "amount_krw": Decimal("3000"), "account_source": "TOSS"})
    portfolio = calculate_portfolio(assets, savings, positions, debts)
    assert portfolio["total_assets"] == Decimal("6500.00")
    assert len(portfolio["warnings"]) == 1


def test_inactive_and_include_rules_are_repository_responsibility():
    """The engine receives only included, active records from the repository."""
    portfolio = calculate_portfolio([], [], [], [])
    assert portfolio["net_worth"] == Decimal("0.00")
