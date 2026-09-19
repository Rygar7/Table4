from datetime import date, timedelta

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_simulate() -> None:
    payload = {
        "income": {"monthly": 3000},
        "fixed_expenses": [{"name": "Rent", "amount": 1000, "essential": True}],
        "flexible_expenses": [],
        "emergency_savings": 2000,
        "investments": [],
        "debts": [],
        "goal": {
            "name": "Trip",
            "target_amount": 5000,
            "current_amount": 500,
            "target_date": (date.today() + timedelta(days=365)).isoformat(),
        },
        "risk_comfort": "balanced",
        "monthly_goal_contribution": 300,
    }
    response = client.post("/api/v1/simulate", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["cash_flow"]["monthly_surplus"] == 2000
    assert len(body["scenarios"]) == 3
