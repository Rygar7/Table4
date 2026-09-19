from backend.app.credit import analyze_credit
from backend.app.credit_coach import _fallback
from backend.app.models import CreditProfile


def sample_profile() -> CreditProfile:
    return CreditProfile.model_validate(
        {
            "bank_accounts": [
                {"name": "Checking", "account_type": "checking", "balance": 900}
            ],
            "credit_cards": [
                {
                    "name": "Rewards",
                    "balance": 1500,
                    "credit_limit": 3000,
                    "apr": 24.9,
                    "minimum_payment": 60,
                    "missed_payments_12_months": 1,
                }
            ],
            "loans": [
                {
                    "name": "Student loan",
                    "balance": 8000,
                    "apr": 5.5,
                    "monthly_payment": 180,
                }
            ],
            "oldest_account_years": 3,
            "recent_credit_applications": 2,
        }
    )


def test_credit_metrics_are_calculated() -> None:
    metrics = analyze_credit(sample_profile())
    assert metrics.overall_utilization_percent == 50.0
    assert metrics.monthly_debt_payments == 240
    assert metrics.available_cash == 900
    assert metrics.missed_payments_12_months == 1
    assert metrics.high_utilization_cards[0].name == "Rewards"


def test_fallback_prioritizes_missed_payments() -> None:
    profile = sample_profile()
    advice = _fallback(profile, analyze_credit(profile))
    assert len(advice.priorities) == 3
    assert advice.priorities[0].title == "Protect on-time payments"
    assert "guarantee" in advice.disclaimer.lower()
