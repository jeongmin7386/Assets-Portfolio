from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_and_dashboard_summary():
    assert client.get("/health").json()["status"] == "ok"
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    payload = response.json()
    assert payload["net_worth"] == payload["total_assets"] - payload["total_debts"]
    assert payload["warnings"] == []


def test_allocation_totals_one_hundred_percent():
    response = client.get("/api/dashboard/allocation")
    assert response.status_code == 200
    items = response.json()
    assert round(sum(item["current_weight"] for item in items), 1) == 100.0
    assert sum(item["target_weight"] for item in items) == 100


def test_read_only_portfolio_routes():
    for path in (
        "/api/accounts", "/api/assets", "/api/savings", "/api/debts",
        "/api/investments/positions", "/api/goals", "/api/history/net-worth?range=1y",
        "/api/sync/status",
    ):
        response = client.get(path)
        assert response.status_code == 200, path
