from datetime import date, timedelta

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.nemotron import _extract_json


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_model_json_parser_ignores_trailing_text() -> None:
    assert _extract_json('{"status": "ok"}\nextra') == {"status": "ok"}


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


def test_credit_advice_endpoint(monkeypatch) -> None:
    from backend.app import main

    monkeypatch.setattr(
        main,
        "create_credit_advice",
        lambda profile, metrics: __import__(
            "backend.app.credit_coach", fromlist=["_fallback"]
        )._fallback(profile, metrics),
    )
    response = client.post(
        "/api/v1/credit/advice",
        json={
            "bank_accounts": [],
            "credit_cards": [
                {
                    "name": "Card",
                    "balance": 500,
                    "credit_limit": 1000,
                    "apr": 20,
                    "minimum_payment": 30,
                    "missed_payments_12_months": 0,
                }
            ],
            "loans": [],
            "oldest_account_years": 2,
            "recent_credit_applications": 0,
        },
    )
    assert response.status_code == 200
    assert response.json()["metrics"]["overall_utilization_percent"] == 50.0
    assert len(response.json()["priorities"]) == 3
