from datetime import date
from enum import Enum

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
