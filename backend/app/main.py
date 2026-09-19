from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .finance import analyze_profile
from .models import FinancialAnalysis, FinancialProfile, PlanResponse
from .nemotron import create_coach


load_dotenv(Path(__file__).resolve().parents[2] / ".env")

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
