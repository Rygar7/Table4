from backend.app.models import SuggestionRequest
from backend.app.trade_ideas import candidate_symbols


def test_short_horizon_uses_fund_candidates() -> None:
    request = SuggestionRequest(time_horizon="under_3_years", risk_comfort="growth")
    assert candidate_symbols(request)[:3] == ["SGOV", "SHY", "BND"]


def test_growth_candidates_still_include_diversified_fund() -> None:
    request = SuggestionRequest(time_horizon="over_7_years", risk_comfort="growth")
    assert "VTI" in candidate_symbols(request)
