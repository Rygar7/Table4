from datetime import date
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class RiskComfort(str, Enum):
    cautious = "cautious"
    balanced = "balanced"
    growth = "growth"


class Income(BaseModel):
    monthly: float = Field(gt=0)


class Expense(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    amount: float = Field(ge=0)
    essential: bool = False


class Investment(BaseModel):
    account_type: str = Field(min_length=1, max_length=80)
    category: str = Field(min_length=1, max_length=120)
    balance: float = Field(ge=0)


class Debt(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    balance: float = Field(ge=0)
    annual_interest_rate: float = Field(ge=0, le=100)
    minimum_payment: float = Field(ge=0)


class Goal(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    target_amount: float = Field(gt=0)
    current_amount: float = Field(ge=0)
    target_date: date

    @field_validator("target_date")
    @classmethod
    def target_must_be_future(cls, value: date) -> date:
        if value <= date.today():
            raise ValueError("target_date must be in the future")
        return value


class FinancialProfile(BaseModel):
    income: Income
    fixed_expenses: list[Expense] = Field(default_factory=list)
    flexible_expenses: list[Expense] = Field(default_factory=list)
    emergency_savings: float = Field(ge=0)
    investments: list[Investment] = Field(default_factory=list)
    debts: list[Debt] = Field(default_factory=list)
    goal: Goal
    risk_comfort: RiskComfort
    monthly_goal_contribution: float = Field(ge=0)


class CashFlowSummary(BaseModel):
    monthly_income: float
    monthly_expenses: float
    monthly_surplus: float
    contribution_affordable: bool


class EmergencyFundSummary(BaseModel):
    essential_monthly_expenses: float
    months_covered: float | None
    target_months: int
    target_amount: float
    gap: float
    status: str


class DebtSummary(BaseModel):
    total_balance: float
    weighted_average_apr: float
    high_interest_debt_detected: bool


class ScenarioResult(BaseModel):
    name: str
    assumed_annual_return: float
    projected_value: float
    target_gap: float
    on_track: bool
    required_monthly_contribution: float


class FinancialAnalysis(BaseModel):
    cash_flow: CashFlowSummary
    emergency_fund: EmergencyFundSummary
    debt: DebtSummary
    goal_name: str
    goal_target_amount: float
    goal_current_amount: float
    months_remaining: int
    scenarios: list[ScenarioResult]
    assumptions_note: str


class CoachPriority(BaseModel):
    rank: int = Field(ge=1, le=5)
    title: str
    reason: str


class CoachResponse(BaseModel):
    primary_obstacle: str
    summary: str
    priorities: list[CoachPriority]
    questions: list[str]
    goal_message: str
    risk_note: str
    generated_by: str = "nemotron"


class PlanResponse(BaseModel):
    analysis: FinancialAnalysis
    coach: CoachResponse
    disclaimer: str


class StockQuote(BaseModel):
    symbol: str
    price: float
    previous_close: float | None
    change: float | None
    change_percent: float | None
    currency: str
    market_feed: str
    as_of: str | None
    disclaimer: str


class StockBar(BaseModel):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class StockHistory(BaseModel):
    symbol: str
    bars: list[StockBar]
    market_feed: str
    disclaimer: str


class StockMetrics(BaseModel):
    latest_price: float
    trading_days_analyzed: int
    period_return_percent: float | None
    annualized_volatility_percent: float | None
    maximum_drawdown_percent: float | None


class StockInsight(BaseModel):
    symbol: str
    risk_level: str
    summary: str
    observations: list[str]
    research_questions: list[str]
    limitations: str
    metrics: StockMetrics
    generated_by: str
    source: str
    source_url: str


class MarketTrend(BaseModel):
    symbol: str
    label: str
    period_return_percent: float | None
    direction: str


class MarketNewsItem(BaseModel):
    headline: str
    summary: str
    source: str
    url: str
    created_at: str
    symbols: list[str]


class PortfolioExample(BaseModel):
    name: str
    risk_level: str
    stock_percent: int
    bond_percent: int
    description: str
    source_url: str


class MarketResearch(BaseModel):
    market_summary: str
    research_ideas: list[str]
    trends: list[MarketTrend]
    portfolio_examples: list[PortfolioExample]
    news: list[MarketNewsItem]
    generated_by: str
    disclaimer: str


class SuggestionRequest(BaseModel):
    time_horizon: Literal["under_3_years", "3_to_7_years", "over_7_years"]
    risk_comfort: RiskComfort
    category: Literal[
        "all",
        "technology",
        "financials",
        "healthcare",
        "consumer",
        "energy",
        "industrials",
        "funds",
    ] = "all"


class TradeIdea(BaseModel):
    symbol: str
    name: str
    instrument_type: str
    category: str
    period_return_percent: float | None
    why_it_appeared: str
    main_risk: str
    next_step: str
    related_news: list[MarketNewsItem]


class SuggestedTrades(BaseModel):
    beginner_summary: str
    ideas: list[TradeIdea]
    news_checked: list[MarketNewsItem]
    generated_by: str
    data_as_of: str
    disclaimer: str


class BankAccount(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    account_type: Literal["checking", "savings"]
    balance: float = Field(ge=0)


class CreditCardAccount(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    balance: float = Field(ge=0)
    credit_limit: float = Field(gt=0)
    apr: float = Field(ge=0, le=100)
    minimum_payment: float = Field(ge=0)
    missed_payments_12_months: int = Field(ge=0, le=12)


class LoanAccount(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    balance: float = Field(ge=0)
    apr: float = Field(ge=0, le=100)
    monthly_payment: float = Field(ge=0)


class CreditProfile(BaseModel):
    credit_score: int | None = Field(default=None, ge=300, le=850)
    bank_accounts: list[BankAccount] = Field(default_factory=list)
    credit_cards: list[CreditCardAccount] = Field(default_factory=list)
    loans: list[LoanAccount] = Field(default_factory=list)
    oldest_account_years: float = Field(default=0, ge=0, le=100)
    recent_credit_applications: int = Field(default=0, ge=0, le=50)


class CardUtilization(BaseModel):
    name: str
    utilization_percent: float


class CreditMetrics(BaseModel):
    total_card_balance: float
    total_credit_limit: float
    overall_utilization_percent: float | None
    high_utilization_cards: list[CardUtilization]
    missed_payments_12_months: int
    total_loan_balance: float
    monthly_debt_payments: float
    available_cash: float


class CreditPriority(BaseModel):
    rank: int = Field(ge=1, le=3)
    title: str
    why: str
    action: str


class CreditAdvice(BaseModel):
    summary: str
    priorities: list[CreditPriority]
    questions: list[str]
    metrics: CreditMetrics
    generated_by: str
    disclaimer: str
    source_links: list[str]
