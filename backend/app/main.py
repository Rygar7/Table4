from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .finance import analyze_profile
from .market import (
    MarketDataError,
    calculate_stock_metrics,
    get_instrument_trends,
    get_news_for_symbols,
    get_stock_history,
    get_stock_quote,
)
from .models import (
    FinancialAnalysis,
    FinancialProfile,
    MarketNewsItem,
    MarketTrend,
    PlanResponse,
    StockHistory,
    StockInsight,
    StockMetrics,
    StockQuote,
    SuggestedTrades,
    SuggestionRequest,
    TaxEstimate,
    TaxEstimateRequest,
)
from .nemotron import create_coach
from .stock_coach import create_stock_insight
from .trade_ideas import INSTRUMENTS, candidate_symbols, create_suggested_trades
from .tax import TaxLookupError, estimate_taxes, lookup_zip


load_dotenv(Path(__file__).resolve().parents[2] / ".env")
PROJECT_ROOT = Path(__file__).resolve().parents[2]
templates = Jinja2Templates(directory=PROJECT_ROOT / "templates")

app = FastAPI(
    title="LifePath AI API",
    version="0.1.0",
    description="Financial scenario calculations with Nemotron-powered educational guidance.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=PROJECT_ROOT / "static"), name="static")


@app.get("/", include_in_schema=False)
def dashboard_page(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/money", include_in_schema=False)
def money_page(request: Request):
    return templates.TemplateResponse(request=request, name="money.html")


@app.get("/calendar", include_in_schema=False)
def calendar_page(request: Request):
    return templates.TemplateResponse(request=request, name="calendar.html")


@app.get("/goals", include_in_schema=False)
def goals_page(request: Request):
    return templates.TemplateResponse(request=request, name="goals.html")


@app.get("/stocks", include_in_schema=False)
def stocks_page(request: Request):
    return templates.TemplateResponse(request=request, name="stocks.html")


@app.get("/ideas", include_in_schema=False)
def ideas_page(request: Request):
    return templates.TemplateResponse(request=request, name="ideas.html")


@app.get("/subscriptions", include_in_schema=False)
def subscriptions_page(request: Request):
    return templates.TemplateResponse(request=request, name="subscriptions.html")


@app.get("/nemotron", include_in_schema=False)
def nemotron_page(request: Request):
    return templates.TemplateResponse(request=request, name="nemotron.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/api/v1/simulate", response_model=FinancialAnalysis)
def simulate(profile: FinancialProfile) -> FinancialAnalysis:
    return analyze_profile(profile)


@app.post("/api/v1/plan", response_model=PlanResponse)
def plan(profile: FinancialProfile) -> PlanResponse:
    analysis = analyze_profile(profile)
    return PlanResponse(
        analysis=analysis,
        coach=create_coach(profile, analysis),
        disclaimer=(
            "LifePath AI provides educational scenarios, not individualized financial, "
            "tax, legal, or investment advice."
        ),
    )


@app.post("/api/v1/tax-estimate", response_model=TaxEstimate)
def tax_estimate(payload: TaxEstimateRequest) -> TaxEstimate:
    try:
        state, state_code = lookup_zip(payload.zip_code)
    except TaxLookupError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    annual_gross = payload.monthly_gross * 12
    values = estimate_taxes(payload.monthly_gross, state_code)
    manual = any(rate is not None for rate in (payload.manual_federal_rate, payload.manual_state_rate, payload.manual_payroll_rate))
    federal = annual_gross * payload.manual_federal_rate / 100 if payload.manual_federal_rate is not None else values["federal"]
    state_tax = annual_gross * payload.manual_state_rate / 100 if payload.manual_state_rate is not None else values["state"]
    payroll = annual_gross * payload.manual_payroll_rate / 100 if payload.manual_payroll_rate is not None else values["payroll"]
    total = federal + state_tax + payroll
    return TaxEstimate(
        tax_year=2026,
        state=state,
        state_code=state_code,
        annual_gross=round(annual_gross, 2),
        federal_annual=round(federal, 2), state_annual=round(state_tax, 2), payroll_annual=round(payroll, 2),
        federal_monthly=round(federal / 12, 2), state_monthly=round(state_tax / 12, 2), payroll_monthly=round(payroll / 12, 2),
        take_home_monthly=round(max(0, payload.monthly_gross - total / 12), 2),
        effective_tax_rate=round(total / annual_gross * 100, 2), used_manual_rates=manual,
        disclaimer="Educational 2026 estimate using simplified single-filer assumptions. Credits, dependents, deductions, local taxes, and special state rules are not included.",
        sources=["IRS 2026 inflation adjustments", "IRS Topic 751", "Tax Foundation 2026 state brackets", "Zippopotam.us ZIP lookup"],
    )


@app.post("/api/v1/market/suggestions", response_model=SuggestedTrades)
def market_suggestions(request: SuggestionRequest) -> SuggestedTrades:
    try:
        symbols = candidate_symbols(request)
        trends = [
            MarketTrend.model_validate(item)
            for item in get_instrument_trends(
                {symbol: INSTRUMENTS[symbol][0] for symbol in symbols}
            )
        ]
        news = [
            MarketNewsItem.model_validate(item)
            for item in get_news_for_symbols(symbols)
        ]
        return create_suggested_trades(request, trends, news)
    except MarketDataError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/v1/stocks/{symbol}", response_model=StockQuote)
def stock_quote(symbol: str) -> StockQuote:
    try:
        return StockQuote.model_validate(get_stock_quote(symbol))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except MarketDataError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/v1/stocks/{symbol}/history", response_model=StockHistory)
def stock_history(symbol: str, days: int = 30) -> StockHistory:
    try:
        return StockHistory.model_validate(get_stock_history(symbol, days))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except MarketDataError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/v1/stocks/{symbol}/insight", response_model=StockInsight)
def stock_insight(symbol: str) -> StockInsight:
    try:
        quote = get_stock_quote(symbol)
        history = get_stock_history(symbol, 30)
        metrics = StockMetrics.model_validate(calculate_stock_metrics(quote, history))
        return create_stock_insight(quote["symbol"], metrics)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except MarketDataError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
