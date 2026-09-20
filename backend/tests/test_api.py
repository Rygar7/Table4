from datetime import date, timedelta

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.nemotron import _extract_json


client = TestClient(app)


def test_dashboard_has_guided_setup() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Finish your financial setup" in response.text
    assert "Main navigation" in response.text


def test_money_page_clarifies_monthly_income() -> None:
    response = client.get("/money")
    assert response.status_code == 200
    assert "Income before taxes each month" in response.text
    assert "Yearly equivalent" in response.text


def test_ai_coach_has_saved_plan_history() -> None:
    response = client.get("/nemotron")
    assert response.status_code == 200
    assert "SAVED PLAN HISTORY" in response.text
    assert "lifepath_plan_history_v1" in response.text


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_subscriptions_page() -> None:
    response = client.get("/subscriptions")
    assert response.status_code == 200
    assert "SUBSCRIPTION TRACKER" in response.text


def test_calendar_page() -> None:
    response = client.get("/calendar")
    assert response.status_code == 200
    assert "SMART MONEY CALENDAR" in response.text
    assert "Build My AI Schedule" in response.text


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
