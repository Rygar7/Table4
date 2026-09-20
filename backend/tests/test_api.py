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
    assert "Home ZIP code" in response.text
    assert "Federal income tax" in response.text
    assert "Total estimated tax" in response.text


def test_accounts_feature_is_removed() -> None:
    assert client.get("/accounts").status_code == 404


def test_ai_coach_has_saved_plan_history() -> None:
    response = client.get("/nemotron")
    assert response.status_code == 200
    assert "SAVED PLAN HISTORY" in response.text
    assert "lifepath_plan_history_v1" in response.text
    assert "Ready to review your finances?" not in response.text
    assert "PLAN CONTROLS" not in response.text
    assert "plan-input-summary" not in response.text


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


def test_tax_estimate_separates_federal_state_and_payroll(monkeypatch) -> None:
    from backend.app import main

    monkeypatch.setattr(main, "lookup_zip", lambda zip_code: ("Pennsylvania", "PA"))
    response = client.post(
        "/api/v1/tax-estimate",
        json={
            "monthly_gross": 5000,
            "zip_code": "15213",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["state_code"] == "PA"
    assert body["federal_monthly"] > 0
    assert body["state_monthly"] > 0
    assert body["payroll_monthly"] > 0
    assert body["take_home_monthly"] < 5000


def test_manual_tax_rates_override_brackets(monkeypatch) -> None:
    from backend.app import main

    monkeypatch.setattr(main, "lookup_zip", lambda zip_code: ("Texas", "TX"))
    response = client.post(
        "/api/v1/tax-estimate",
        json={
            "monthly_gross": 5000,
            "zip_code": "78701",
            "manual_federal_rate": 10,
            "manual_state_rate": 2,
            "manual_payroll_rate": 5,
        },
    )
    assert response.status_code == 200
    assert response.json()["federal_monthly"] == 500
    assert response.json()["state_monthly"] == 100
    assert response.json()["payroll_monthly"] == 250
