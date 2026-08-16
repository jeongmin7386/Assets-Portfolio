from datetime import datetime, timezone
from decimal import Decimal
from typing import Any


def decimal_value(value: Any) -> Decimal:
    return Decimal(str(value or "0"))


def map_holding(item: dict[str, Any], usd_krw: Decimal) -> dict[str, Any]:
    """Map only fields documented by Toss Securities HoldingsItem."""
    currency = item["currency"]
    fx = usd_krw if currency == "USD" else Decimal("1")
    market_value = decimal_value(item["marketValue"]["amount"])
    purchase_amount = decimal_value(item["marketValue"]["purchaseAmount"])
    pnl = decimal_value(item["profitLoss"]["amount"])
    return {
        "symbol": item["symbol"],
        "name": item["name"],
        "market": item["marketCountry"],
        "security_type": "UNKNOWN",
        "currency": currency,
        "quantity": decimal_value(item["quantity"]),
        "average_price": decimal_value(item["averagePurchasePrice"]),
        "cost_basis": purchase_amount,
        "current_price": decimal_value(item["lastPrice"]),
        "market_value_native": market_value,
        "market_value_krw": market_value * fx,
        "unrealized_pnl_native": pnl,
        "unrealized_pnl_krw": pnl * fx,
        "return_rate": decimal_value(item["profitLoss"]["rate"]) * Decimal("100"),
        "synced_at": datetime.now(timezone.utc),
    }
