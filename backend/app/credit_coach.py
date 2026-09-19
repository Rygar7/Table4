import json
import os

from openai import OpenAI

from .models import CreditAdvice, CreditMetrics, CreditPriority, CreditProfile
from .nemotron import _extract_json


SOURCE_LINKS = [
    "https://www.myfico.com/credit-education/whats-in-your-credit-score",
    "https://www.myfico.com/credit-education/credit-scores/new-credit",
]
DISCLAIMER = (
    "Educational guidance only. Credit scoring formulas vary, and no action can guarantee "
    "a particular score change. Verify account details with your lenders and credit reports."
)
ALLOWED_CATEGORIES = {
    "payment_history": "Protect on-time payments",
    "utilization": "Lower card utilization",
    "emergency_cash": "Build a payment cushion",
    "debt_payment_load": "Review expensive debt",
    "recent_credit": "Pause unnecessary applications",
    "review_credit_reports": "Review your credit reports",
}


def _short(value: object, maximum_words: int) -> str:
    words = str(value or "").split()
    return " ".join(words[:maximum_words]).strip()


def _fallback_priorities(
    profile: CreditProfile, metrics: CreditMetrics
) -> list[CreditPriority]:
    candidates: list[tuple[int, str, str, str]] = []
    if metrics.missed_payments_12_months:
        candidates.append((
            100,
            "Protect on-time payments",
            f"You entered {metrics.missed_payments_12_months} missed payment(s) in the last year.",
            "Turn on due-date reminders or autopay for at least the minimum, while keeping enough cash in the payment account.",
        ))
    if metrics.overall_utilization_percent is not None and metrics.overall_utilization_percent >= 30:
        candidates.append((
            90,
            "Lower card utilization",
            f"Your entered card balances use {metrics.overall_utilization_percent:.1f}% of your total limits.",
            "Choose one high-utilization card and make a realistic extra payment before adding new charges.",
        ))
    if metrics.available_cash < metrics.monthly_debt_payments:
        candidates.append((
            80,
            "Build a payment cushion",
            "Your entered cash is below one month of entered debt payments.",
            "Set aside a small buffer in checking or savings to reduce the chance of a missed payment.",
        ))
    if profile.recent_credit_applications >= 2:
        candidates.append((
            70,
            "Pause unnecessary applications",
            f"You entered {profile.recent_credit_applications} recent credit applications.",
            "Avoid applying for more credit unless you need it and understand the terms.",
        ))
    if metrics.total_card_balance + metrics.total_loan_balance > 0:
        candidates.append((
            60,
            "Review expensive debt",
            "Interest can make balances harder to reduce even when payments are on time.",
            "List debts by APR, keep every minimum current, and review the highest-rate balance first.",
        ))
    candidates.append((
        40,
        "Review your credit reports",
        "Your app entries may not include every item used by a credit-scoring model.",
        "Check your official credit reports and dispute only information that is genuinely inaccurate.",
    ))
    candidates.sort(key=lambda item: item[0], reverse=True)
    return [
        CreditPriority(rank=index, title=title, why=why, action=action)
        for index, (_, title, why, action) in enumerate(candidates[:3], 1)
    ]


def _fallback(profile: CreditProfile, metrics: CreditMetrics) -> CreditAdvice:
    return CreditAdvice(
        summary="Focus first on reliable payments and manageable card balances.",
        priorities=_fallback_priorities(profile, metrics),
        questions=["Are all of your account balances and due dates current?"],
        metrics=metrics,
        generated_by="fallback",
        disclaimer=DISCLAIMER,
        source_links=SOURCE_LINKS,
    )


def create_credit_advice(
    profile: CreditProfile, metrics: CreditMetrics
) -> CreditAdvice:
    payload = {
        "optional_current_score": profile.credit_score,
        "oldest_account_years": profile.oldest_account_years,
        "recent_credit_applications": profile.recent_credit_applications,
        "verified_calculated_metrics": metrics.model_dump(),
    }
    system_prompt = """
You are a cautious credit-priority ranking component for a beginner finance app. Rank
exactly three useful next steps using only the supplied facts. Allowed categories are:
payment_history, utilization, emergency_cash, debt_payment_load, recent_credit, and
review_credit_reports. Payment history generally deserves the highest priority when a
missed payment is reported. Income and living expenses were not provided: never compare
payments or cash to income, expenses, or an emergency-fund target. Do not predict point
changes, guarantee results, invent lender actions, recommend draining cash reserves, or tell
someone to open or close an account just for credit mix. Never advise disputing accurate
information. Keep each field plain and under 30 words. Return only JSON:
summary, priorities, questions. Each priority needs category, why, and action. Questions
must contain at most two short items.
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
                {"role": "user", "content": json.dumps(payload)},
            ],
            temperature=0.1,
            max_tokens=800,
            extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        )
        parsed = _extract_json(response.choices[0].message.content or "{}")
        raw_priorities = list(parsed.get("priorities", []))
        categories = [item.get("category") for item in raw_priorities]
        if (
            len(raw_priorities) != 3
            or len(set(categories)) != 3
            or not set(categories) <= set(ALLOWED_CATEGORIES)
        ):
            raise ValueError("Nemotron returned unsupported credit priorities")
        priorities = [
            CreditPriority(
                rank=index,
                title=ALLOWED_CATEGORIES[item["category"]],
                why=_short(item.get("why"), 30),
                action=_short(item.get("action"), 30),
            )
            for index, item in enumerate(raw_priorities, 1)
        ]
        return CreditAdvice(
            summary=_short(parsed.get("summary"), 35),
            priorities=priorities,
            questions=[_short(item, 25) for item in list(parsed.get("questions", []))[:2]],
            metrics=metrics,
            generated_by="nemotron",
            disclaimer=DISCLAIMER,
            source_links=SOURCE_LINKS,
        )
    except Exception:
        return _fallback(profile, metrics)
