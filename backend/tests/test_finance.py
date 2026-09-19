from datetime import date, timedelta

from backend.app.finance import analyze_profile
from backend.app.models import FinancialProfile


def profile_data() -> dict:
    return {
        "income": {"monthly": 4200},
        "fixed_expenses": [
            {"name": "Rent", "amount": 1400, "essential": True},
            {"name": "Phone", "amount": 80, "essential": True},
        ],
        "flexible_expenses": [
            {"name": "Food", "amount": 500, "essential": True},
            {"name": "Entertainment", "amount": 250, "essential": False},
        ],
        "emergency_savings": 3000,
        "investments": [],
        "debts": [
            {
                "name": "Credit card",
                "balance": 1800,
                "annual_interest_rate": 22.5,
                "minimum_payment": 75,
            }
        ],
        "goal": {
            "name": "Buy a car",
            "target_amount": 12000,
            "current_amount": 2000,
            "target_date": (date.today() + timedelta(days=730)).isoformat(),
        },
        "risk_comfort": "balanced",
        "monthly_goal_contribution": 300,
    }


def test_cash_flow_and_emergency_fund() -> None:
    analysis = analyze_profile(FinancialProfile(**profile_data()))
    assert analysis.cash_flow.monthly_expenses == 2230
    assert analysis.cash_flow.monthly_surplus == 1970
    assert analysis.emergency_fund.essential_monthly_expenses == 1980
    assert analysis.emergency_fund.status == "below_target"


def test_scenarios_are_ordered_by_return() -> None:
    analysis = analyze_profile(FinancialProfile(**profile_data()))
    projected = [scenario.projected_value for scenario in analysis.scenarios]
    assert projected == sorted(projected)
    assert [scenario.name for scenario in analysis.scenarios] == [
        "conservative",
        "balanced",
        "growth",
    ]


def test_high_interest_debt_is_detected() -> None:
    analysis = analyze_profile(FinancialProfile(**profile_data()))
    assert analysis.debt.high_interest_debt_detected is True
    assert analysis.debt.total_balance == 1800
