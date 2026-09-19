import math
from datetime import date

from .models import (
    CashFlowSummary,
    DebtSummary,
    EmergencyFundSummary,
    FinancialAnalysis,
    FinancialProfile,
    ScenarioResult,
)


SCENARIO_RETURNS = {
    "conservative": 0.02,
    "balanced": 0.05,
    "growth": 0.08,
}
EMERGENCY_TARGET_MONTHS = 3
HIGH_INTEREST_APR = 10.0


def _money(value: float) -> float:
    return round(value, 2)


def _months_until(target: date) -> int:
    days = (target - date.today()).days
    return max(1, math.ceil(days / 30.4375))


def _monthly_rate(annual_return: float) -> float:
    return (1 + annual_return) ** (1 / 12) - 1


def _future_value(current: float, contribution: float, months: int, annual_return: float) -> float:
    rate = _monthly_rate(annual_return)
    growth = (1 + rate) ** months
    contributions = contribution * ((growth - 1) / rate) if rate else contribution * months
    return current * growth + contributions


def _required_contribution(target: float, current: float, months: int, annual_return: float) -> float:
    rate = _monthly_rate(annual_return)
    growth = (1 + rate) ** months
    remaining = target - current * growth
    if remaining <= 0:
        return 0.0
    annuity_factor = ((growth - 1) / rate) if rate else months
    return remaining / annuity_factor


def analyze_profile(profile: FinancialProfile) -> FinancialAnalysis:
    all_expenses = profile.fixed_expenses + profile.flexible_expenses
    total_expenses = sum(item.amount for item in all_expenses)
    essential_expenses = sum(item.amount for item in all_expenses if item.essential)
    surplus = profile.income.monthly - total_expenses

    if essential_expenses > 0:
        months_covered = profile.emergency_savings / essential_expenses
        emergency_target = essential_expenses * EMERGENCY_TARGET_MONTHS
    else:
        months_covered = None
        emergency_target = 0.0
    emergency_gap = max(0.0, emergency_target - profile.emergency_savings)

    total_debt = sum(item.balance for item in profile.debts)
    weighted_apr = (
        sum(item.balance * item.annual_interest_rate for item in profile.debts) / total_debt
        if total_debt
        else 0.0
    )
    high_interest = any(
        item.balance > 0 and item.annual_interest_rate >= HIGH_INTEREST_APR
        for item in profile.debts
    )

    months = _months_until(profile.goal.target_date)
    scenarios = []
    for name, annual_return in SCENARIO_RETURNS.items():
        projected = _future_value(
            profile.goal.current_amount,
            profile.monthly_goal_contribution,
            months,
            annual_return,
        )
        scenarios.append(
            ScenarioResult(
                name=name,
                assumed_annual_return=annual_return,
                projected_value=_money(projected),
                target_gap=_money(max(0.0, profile.goal.target_amount - projected)),
                on_track=projected >= profile.goal.target_amount,
                required_monthly_contribution=_money(
                    _required_contribution(
                        profile.goal.target_amount,
                        profile.goal.current_amount,
                        months,
                        annual_return,
                    )
                ),
            )
        )

    return FinancialAnalysis(
        cash_flow=CashFlowSummary(
            monthly_income=_money(profile.income.monthly),
            monthly_expenses=_money(total_expenses),
            monthly_surplus=_money(surplus),
            contribution_affordable=surplus >= profile.monthly_goal_contribution,
        ),
        emergency_fund=EmergencyFundSummary(
            essential_monthly_expenses=_money(essential_expenses),
            months_covered=round(months_covered, 2) if months_covered is not None else None,
            target_months=EMERGENCY_TARGET_MONTHS,
            target_amount=_money(emergency_target),
            gap=_money(emergency_gap),
            status="on_target" if emergency_gap == 0 else "below_target",
        ),
        debt=DebtSummary(
            total_balance=_money(total_debt),
            weighted_average_apr=round(weighted_apr, 2),
            high_interest_debt_detected=high_interest,
        ),
        goal_name=profile.goal.name,
        goal_target_amount=_money(profile.goal.target_amount),
        goal_current_amount=_money(profile.goal.current_amount),
        months_remaining=months,
        scenarios=scenarios,
        assumptions_note=(
            "Scenario returns are hypothetical educational assumptions, not predictions or guarantees."
        ),
    )
