import os
import re
import time
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from math import sqrt
from statistics import stdev

import httpx


ALPACA_DATA_URL = "https://data.alpaca.markets/v2"
SYMBOL_PATTERN = re.compile(r"^[A-Z][A-Z0-9.-]{0,9}$")


class MarketDataError(RuntimeError):
    pass


def normalize_symbol(symbol: str) -> str:
    normalized = symbol.strip().upper()
    if not SYMBOL_PATTERN.fullmatch(normalized):
        raise ValueError("Enter a valid stock symbol such as AAPL or NVDA.")
    return normalized


def _headers() -> dict[str, str]:
    key = os.getenv("ALPACA_API_KEY")
    secret = os.getenv("ALPACA_API_SECRET")
    if not key or not secret:
        raise MarketDataError("Alpaca credentials are not configured.")
    return {
        "APCA-API-KEY-ID": key,
        "APCA-API-SECRET-KEY": secret,
    }


def _get(path: str, params: dict[str, str | int]) -> dict:
    try:
        response = httpx.get(
            f"{ALPACA_DATA_URL}{path}",
            params=params,
            headers=_headers(),
            timeout=15,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise MarketDataError("Stock symbol was not found.") from exc
        raise MarketDataError("The stock-data provider rejected the request.") from exc
    except httpx.HTTPError as exc:
        raise MarketDataError("The stock-data provider is temporarily unavailable.") from exc
    return response.json()


def get_stock_quote(symbol: str) -> dict:
    normalized = normalize_symbol(symbol)
    return _get_stock_quote_cached(normalized, int(time.time() // 30))


@lru_cache(maxsize=512)
def _get_stock_quote_cached(normalized: str, _cache_window: int) -> dict:
    payload = _get(
        "/stocks/snapshots",
        {"symbols": normalized, "feed": "iex"},
    )
    snapshot = payload.get(normalized)
    if not snapshot:
        raise MarketDataError("Stock symbol was not found.")

    latest_trade = snapshot.get("latestTrade") or {}
    minute_bar = snapshot.get("minuteBar") or {}
    daily_bar = snapshot.get("dailyBar") or {}
    previous_bar = snapshot.get("prevDailyBar") or {}
    price = latest_trade.get("p") or minute_bar.get("c") or daily_bar.get("c")
    previous_close = previous_bar.get("c")
    if price is None:
        raise MarketDataError("No current price is available for this symbol.")

    change = None
    change_percent = None
    if previous_close:
        change = round(float(price) - float(previous_close), 2)
        change_percent = round(change / float(previous_close) * 100, 2)

    return {
        "symbol": normalized,
        "price": round(float(price), 2),
        "previous_close": round(float(previous_close), 2) if previous_close else None,
        "change": change,
        "change_percent": change_percent,
        "currency": "USD",
        "market_feed": "IEX",
        "as_of": latest_trade.get("t") or minute_bar.get("t") or daily_bar.get("t"),
        "disclaimer": "Market data is informational and may be delayed or incomplete.",
    }


def get_stock_history(symbol: str, days: int = 30) -> dict:
    normalized = normalize_symbol(symbol)
    days = max(1, min(days, 365))
    return _get_stock_history_cached(normalized, days, int(time.time() // 300))


@lru_cache(maxsize=512)
def _get_stock_history_cached(normalized: str, days: int, _cache_window: int) -> dict:
    start = datetime.now(timezone.utc) - timedelta(days=days * 2)
    payload = _get(
        f"/stocks/{normalized}/bars",
        {
            "timeframe": "1Day",
            "start": start.isoformat(),
            "limit": days,
            "adjustment": "all",
            "feed": "iex",
            "sort": "desc",
        },
    )
    bars = list(reversed(payload.get("bars", [])))
    return {
        "symbol": normalized,
        "bars": [
            {
                "timestamp": bar["t"],
                "open": bar["o"],
                "high": bar["h"],
                "low": bar["l"],
                "close": bar["c"],
                "volume": bar["v"],
            }
            for bar in bars
        ],
        "market_feed": "IEX",
        "disclaimer": "Historical market data is informational and may be delayed or incomplete.",
    }


def calculate_stock_metrics(quote: dict, history: dict) -> dict:
    closes = [float(bar["close"]) for bar in history["bars"] if bar.get("close")]
    returns = [closes[index] / closes[index - 1] - 1 for index in range(1, len(closes))]

    period_return = None
    if len(closes) >= 2 and closes[0]:
        period_return = round((closes[-1] / closes[0] - 1) * 100, 2)

    volatility = None
    if len(returns) >= 2:
        volatility = round(stdev(returns) * sqrt(252) * 100, 2)

    maximum_drawdown = None
    if closes:
        peak = closes[0]
        worst = 0.0
        for close in closes:
            peak = max(peak, close)
            worst = min(worst, close / peak - 1)
        maximum_drawdown = round(worst * 100, 2)

    return {
        "latest_price": quote["price"],
        "trading_days_analyzed": len(closes),
        "period_return_percent": period_return,
        "annualized_volatility_percent": volatility,
        "maximum_drawdown_percent": maximum_drawdown,
    }
