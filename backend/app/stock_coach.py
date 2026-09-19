import json
import os

from openai import OpenAI

from .models import StockInsight, StockMetrics
from .nemotron import _extract_json


def _fallback(symbol: str, metrics: StockMetrics) -> StockInsight:
    volatility = metrics.annualized_volatility_percent
    if volatility is None:
        risk_level = "insufficient_data"
    elif volatility >= 45:
        risk_level = "high"
    elif volatility >= 25:
        risk_level = "moderate"
    else:
        risk_level = "lower"

    return StockInsight(
        symbol=symbol,
        risk_level=risk_level,
        summary="Review the recent price range in the context of a diversified, long-term plan.",
        observations=[
            "Recent performance is historical and does not predict future returns.",
            "A single price history cannot explain the company’s financial health or valuation.",
        ],
        research_questions=[
            "How would a loss in this position affect your emergency fund and near-term goals?",
            "Have you reviewed the company’s filings, business risks, and valuation?",
        ],
        limitations="This is educational market research, not a recommendation to buy or sell.",
        metrics=metrics,
        generated_by="fallback",
        source="Alpaca Market Data (IEX feed)",
        source_url="https://docs.alpaca.markets/docs/about-market-data-api",
    )


def create_stock_insight(symbol: str, metrics: StockMetrics) -> StockInsight:
    system_prompt = """
You are the risk-classification component in an educational financial application.
Using only the verified market metrics provided, classify recent price risk as lower,
moderate, high, or insufficient_data. Explain what the measurements show and provide
research questions. Never tell the user to buy, sell, hold, time the market, or expect a
future return. Never invent company facts, news, fundamentals, or prices. Return only JSON
with: risk_level, summary, observations, research_questions, limitations. observations and
research_questions must be arrays with two or three concise items.
""".strip()
    try:
        client = OpenAI(
            base_url=os.environ["NVIDIA_BASE_URL"],
            api_key=os.environ["NVIDIA_API_KEY"],
        )
        response = client.chat.completions.create(
            model=os.environ["NVIDIA_MODEL"],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(metrics.model_dump())},
            ],
            temperature=0.1,
            max_tokens=700,
            extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        )
        parsed = _extract_json(response.choices[0].message.content or "{}")
        if parsed.get("risk_level") not in {"lower", "moderate", "high", "insufficient_data"}:
            raise ValueError("Unsupported risk level")
        parsed["observations"] = list(parsed.get("observations", []))[:3]
        parsed["research_questions"] = list(parsed.get("research_questions", []))[:3]
        if isinstance(parsed.get("limitations"), list):
            parsed["limitations"] = " ".join(parsed["limitations"])
        return StockInsight(
            symbol=symbol,
            metrics=metrics,
            generated_by="nemotron",
            source="Alpaca Market Data (IEX feed)",
            source_url="https://docs.alpaca.markets/docs/about-market-data-api",
            **parsed,
        )
    except Exception:
        return _fallback(symbol, metrics)
