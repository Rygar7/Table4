import json
import os
import re

from openai import OpenAI

from .models import CoachPriority, CoachResponse, FinancialAnalysis, FinancialProfile


ALLOWED_OBSTACLES = {
    "negative_cash_flow",
    "emergency_fund_gap",
    "high_interest_debt",
    "goal_contribution_gap",
    "goal_timeline_too_short",
    "on_track",
}


def _client() -> OpenAI:
    return OpenAI(
        base_url=os.environ["NVIDIA_BASE_URL"],
        api_key=os.environ["NVIDIA_API_KEY"],
    )


def _extract_json(text: str) -> dict:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE)
    return json.loads(cleaned)


def _fallback_coach(analysis: FinancialAnalysis) -> CoachResponse:
    if analysis.cash_flow.monthly_surplus < 0:
        obstacle = "negative_cash_flow"
        title = "Stabilize monthly cash flow"
        reason = "Current expenses are greater than monthly income."
    elif analysis.debt.high_interest_debt_detected:
        obstacle = "high_interest_debt"
        title = "Review high-interest debt"
        reason = "High-interest balances can slow progress toward the goal."
    elif analysis.emergency_fund.status == "below_target":
        obstacle = "emergency_fund_gap"
        title = "Build an emergency cushion"
        reason = "Emergency savings currently cover less than the educational target."
    elif not analysis.scenarios[1].on_track:
        obstacle = "goal_contribution_gap"
        title = "Revisit the contribution or timeline"
        reason = "The balanced scenario does not reach the goal by the selected date."
    else:
        obstacle = "on_track"
        title = "Maintain the current plan"
        reason = "The balanced scenario reaches the selected goal."

    return CoachResponse(
        primary_obstacle=obstacle,
        summary=reason,
        priorities=[CoachPriority(rank=1, title=title, reason=reason)],
        questions=["What small change would feel realistic to maintain each month?"],
        goal_message=reason,
        risk_note="All projections are hypothetical and actual results may be higher or lower.",
        generated_by="fallback",
    )


def create_coach(profile: FinancialProfile, analysis: FinancialAnalysis) -> CoachResponse:
    prompt_payload = {
        "risk_comfort": profile.risk_comfort.value,
        "monthly_goal_contribution": profile.monthly_goal_contribution,
        "analysis": analysis.model_dump(mode="json"),
    }
    system_prompt = """
You are the decision component inside LifePath AI, an educational financial simulator.
Classify the user's primary obstacle, rank up to three educational next steps, and explain
the tradeoffs using only the verified calculations provided. Do not recalculate numbers,
recommend individual securities, guarantee returns, shame the user, or use pressure tactics.
Return only valid JSON with these keys: primary_obstacle, summary, priorities, questions,
goal_message, risk_note. priorities must contain rank, title, and reason. primary_obstacle
must be one of: negative_cash_flow, emergency_fund_gap, high_interest_debt,
goal_contribution_gap, goal_timeline_too_short, on_track.
""".strip()

    try:
        response = _client().chat.completions.create(
            model=os.environ["NVIDIA_MODEL"],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(prompt_payload)},
            ],
            temperature=0.1,
            max_tokens=1000,
            extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        )
        raw = response.choices[0].message.content or "{}"
        parsed = _extract_json(raw)
        coach = CoachResponse(**parsed, generated_by="nemotron")
        if coach.primary_obstacle not in ALLOWED_OBSTACLES:
            raise ValueError("Nemotron returned an unsupported obstacle")
        return coach
    except Exception:
        return _fallback_coach(analysis)
