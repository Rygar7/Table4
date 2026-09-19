import pytest

from backend.app.market import calculate_stock_metrics, normalize_symbol


def test_normalize_symbol() -> None:
    assert normalize_symbol(" nvda ") == "NVDA"


@pytest.mark.parametrize("symbol", ["", "AAPL!", "../../env", "TOO-LONG-SYMBOL"])
def test_invalid_symbol_is_rejected(symbol: str) -> None:
    with pytest.raises(ValueError):
        normalize_symbol(symbol)


def test_calculate_stock_metrics() -> None:
    quote = {"price": 110.0}
    history = {
        "bars": [
            {"close": 100.0},
            {"close": 105.0},
            {"close": 110.0},
        ]
    }
    metrics = calculate_stock_metrics(quote, history)
    assert metrics["latest_price"] == 110.0
    assert metrics["trading_days_analyzed"] == 3
    assert metrics["period_return_percent"] == 10.0
    assert metrics["maximum_drawdown_percent"] == 0.0
