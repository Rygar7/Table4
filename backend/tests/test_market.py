import pytest

from backend.app.market import normalize_symbol


def test_normalize_symbol() -> None:
    assert normalize_symbol(" nvda ") == "NVDA"


@pytest.mark.parametrize("symbol", ["", "AAPL!", "../../env", "TOO-LONG-SYMBOL"])
def test_invalid_symbol_is_rejected(symbol: str) -> None:
    with pytest.raises(ValueError):
        normalize_symbol(symbol)
