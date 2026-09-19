from backend.app.models import SuggestionRequest
from backend.app.trade_ideas import candidate_symbols


def test_short_horizon_uses_fund_candidates() -> None:
    request = SuggestionRequest(time_horizon="under_3_years", risk_comfort="growth")
    assert candidate_symbols(request)[:3] == ["SGOV", "SHY", "BND"]


def test_growth_candidates_still_include_diversified_fund() -> None:
    request = SuggestionRequest(time_horizon="over_7_years", risk_comfort="growth")
    assert "VTI" in candidate_symbols(request)


def test_technology_category_only_uses_technology_companies() -> None:
    request = SuggestionRequest(
        time_horizon="over_7_years",
        risk_comfort="growth",
        category="technology",
    )
    assert candidate_symbols(request) == ["MSFT", "NVDA", "AAPL", "GOOGL", "META", "AMZN"]


def test_fund_category_keeps_short_horizon_conservative() -> None:
    request = SuggestionRequest(
        time_horizon="under_3_years",
        risk_comfort="growth",
        category="funds",
    )
    assert candidate_symbols(request)[:3] == ["SGOV", "SHY", "BND"]
