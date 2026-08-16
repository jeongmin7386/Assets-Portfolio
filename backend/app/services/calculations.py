from collections import defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Any


ZERO = Decimal("0")
HUNDRED = Decimal("100")
MONEY_QUANT = Decimal("0.01")
RATE_QUANT = Decimal("0.01")
SUPPORTED_CURRENCIES = {"KRW", "USD"}
ASSET_CLASSES = ("현금", "예적금", "ETF", "개별주식", "금", "보증금", "기타자산")


def money(value: Decimal | int | str | float) -> Decimal:
    return Decimal(str(value)).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def rate(value: Decimal | int | str | float) -> Decimal:
    return Decimal(str(value)).quantize(RATE_QUANT, rounding=ROUND_HALF_UP)


def convert_currency(amount: Decimal, currency: str, usd_krw: Decimal | None) -> Decimal:
    if currency == "KRW":
        return money(amount)
    if currency == "USD" and usd_krw is not None:
        return money(amount * usd_krw)
    raise ValueError(f"Unsupported currency or missing rate: {currency}")


def detect_double_counting(manual_assets: list[dict[str, Any]]) -> list[str]:
    warnings = []
    for item in manual_assets:
        if item.get("account_source") == "TOSS" and money(item.get("amount_krw", ZERO)) > ZERO:
            warnings.append(f"{item['name']}: TOSS 계좌의 수동자산은 중복 합산에서 제외되었습니다.")
    return warnings


def calculate_portfolio(
    manual_assets: list[dict[str, Any]],
    savings: list[dict[str, Any]],
    positions: list[dict[str, Any]],
    debts: list[dict[str, Any]],
) -> dict[str, Any]:
    warnings = detect_double_counting(manual_assets)
    class_values: dict[str, Decimal] = defaultdict(lambda: ZERO)

    for item in manual_assets:
        if item.get("account_source") == "TOSS":
            continue
        class_values[item.get("asset_class") or "기타자산"] += money(item["amount_krw"])
    for item in savings:
        class_values["예적금"] += money(item["current_balance"])
    for item in positions:
        asset_class = item.get("security_type")
        if asset_class not in {"ETF", "개별주식"}:
            asset_class = "기타자산"
        class_values[asset_class] += money(item["market_value_krw"])

    total_assets = sum(class_values.values(), ZERO)
    total_debts = sum((money(item["current_balance"]) for item in debts), ZERO)
    return {
        "class_values": {key: money(class_values[key]) for key in ASSET_CLASSES},
        "manual_assets_value": money(sum((money(item["amount_krw"]) for item in manual_assets if item.get("account_source") != "TOSS"), ZERO)),
        "savings_value": money(sum((money(item["current_balance"]) for item in savings), ZERO)),
        "investment_value": money(sum((money(item["market_value_krw"]) for item in positions), ZERO)),
        "total_assets": money(total_assets),
        "total_debts": money(total_debts),
        "net_worth": money(total_assets - total_debts),
        "warnings": warnings,
    }


def calculate_allocation(
    class_values: dict[str, Decimal], targets: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    total = sum(class_values.values(), ZERO)
    target_map = {item["asset_class"]: item for item in targets}
    result = []
    for asset_class in ASSET_CLASSES:
        value = money(class_values.get(asset_class, ZERO))
        current_weight = rate(value / total * HUNDRED) if total else ZERO
        target = target_map.get(asset_class, {})
        target_weight = rate(target.get("target_weight", ZERO))
        minimum = target.get("minimum_weight")
        maximum = target.get("maximum_weight")
        target_amount = money(total * target_weight / HUNDRED)
        if minimum is not None and current_weight < rate(minimum):
            status = "UNDERWEIGHT"
        elif maximum is not None and current_weight > rate(maximum):
            status = "OVERWEIGHT"
        else:
            status = "NORMAL"
        result.append({
            "asset_class": asset_class,
            "current_value": value,
            "current_weight": current_weight,
            "target_weight": target_weight,
            "minimum_weight": rate(minimum) if minimum is not None else None,
            "maximum_weight": rate(maximum) if maximum is not None else None,
            "weight_difference": rate(current_weight - target_weight),
            "target_amount": target_amount,
            "amount_difference": money(value - target_amount),
            "status": status,
        })
    return result


def calculate_savings_projection(item: dict[str, Any], today: date) -> dict[str, Any]:
    opened_at = item.get("opened_at")
    maturity_at = item.get("maturity_at")
    if opened_at and maturity_at and maturity_at < opened_at:
        raise ValueError("maturity_at must be on or after opened_at")
    days_remaining = max((maturity_at - today).days, 0) if maturity_at else 0
    months_remaining = max(round(days_remaining / 30.4375), 0)
    current_balance = money(item.get("current_balance", ZERO))
    contribution = money(item.get("monthly_contribution", ZERO))
    annual_rate = Decimal(str(item.get("base_rate", ZERO))) + Decimal(str(item.get("bonus_rate", ZERO)))
    future_contributions = contribution * months_remaining
    years = Decimal(days_remaining) / Decimal("365")
    estimated_interest_before_tax = (current_balance + future_contributions / Decimal("2")) * annual_rate / HUNDRED * years
    tax_rate = Decimal("0.154") if item.get("tax_type") not in {"TAX_FREE", "비과세"} else ZERO
    after_tax_interest = money(estimated_interest_before_tax * (Decimal("1") - tax_rate))
    return {
        **item,
        "annual_rate": rate(annual_rate),
        "days_remaining": days_remaining,
        "months_remaining": months_remaining,
        "estimated_interest_after_tax": after_tax_interest,
        "estimated_maturity_amount": money(current_balance + future_contributions + after_tax_interest),
        "is_estimated": True,
    }


def goal_current_value(goal_type: str, portfolio: dict[str, Any]) -> Decimal:
    normalized = goal_type.upper()
    if goal_type == "순자산" or normalized == "NET_WORTH":
        return portfolio["net_worth"]
    if goal_type == "투자" or normalized == "INVESTMENT":
        return portfolio["investment_value"]
    if goal_type == "예적금" or normalized == "SAVINGS":
        return portfolio["savings_value"]
    if goal_type == "총자산" or normalized == "TOTAL_ASSETS":
        return portfolio["total_assets"]
    if goal_type == "부채감소" or normalized == "DEBT_REDUCTION":
        return portfolio["total_debts"]
    return portfolio["class_values"].get("현금", ZERO)
