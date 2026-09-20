import pytest

from backend.app.tax import estimate_taxes, progressive_tax


def test_progressive_tax_only_applies_each_marginal_rate() -> None:
    assert progressive_tax(20_000, [(0, 0.10), (10_000, 0.20)]) == pytest.approx(3_000)


def test_2026_pennsylvania_estimate_separates_tax_types() -> None:
    result = estimate_taxes(5_000, "PA")
    assert result["federal"] == pytest.approx(5_020)
    assert result["state"] == pytest.approx(1_842)
    assert result["payroll"] == pytest.approx(4_590)
