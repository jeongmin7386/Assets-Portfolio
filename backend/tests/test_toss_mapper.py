from decimal import Decimal

from app.services.toss.mapper import map_holding


def test_official_toss_holdings_schema_mapping():
    result = map_holding(
        {
            "symbol": "AAPL", "name": "Apple Inc.", "marketCountry": "US", "currency": "USD",
            "quantity": "10", "lastPrice": "178.5", "averagePurchasePrice": "155.3",
            "marketValue": {"purchaseAmount": "1553", "amount": "1785", "amountAfterCost": "1771.43"},
            "profitLoss": {"amount": "232", "amountAfterCost": "218.43", "rate": "0.1494", "rateAfterCost": "0.1406"},
            "dailyProfitLoss": {"amount": "25", "rate": "0.0142"},
            "cost": {"commission": "3.57", "tax": "10"},
        },
        Decimal("1380.5"),
    )
    assert result["market_value_krw"] == Decimal("2464192.5")
    assert result["return_rate"] == Decimal("14.9400")
    assert result["security_type"] == "UNKNOWN"
