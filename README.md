# Table4
Finance app with Nemotron

## LifePath AI backend

The backend uses Python and FastAPI for financial calculations. NVIDIA
Nemotron receives only verified summaries and returns structured educational guidance.

### Run locally

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/uvicorn backend.app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the interactive API documentation.

### Endpoints

- `GET /health` checks whether the API is running.
- `POST /api/v1/simulate` returns cash-flow, emergency-fund, debt, and goal scenarios.
- `POST /api/v1/plan` returns the calculations plus Nemotron guidance.
- `POST /api/v1/tax-estimate` estimates federal, state, and payroll taxes from monthly income and ZIP code.
- `GET /api/v1/stocks/{symbol}` returns the latest Alpaca/IEX stock quote.
- `GET /api/v1/stocks/{symbol}/history` returns recent daily price history.
- `GET /api/v1/stocks/{symbol}/insight` calculates recent risk metrics and asks Nemotron to explain them.
- `POST /api/v1/market/suggestions` returns a three-item beginner research shortlist
  by market category, based on time horizon, risk comfort, verified trends, and current sourced news.

Open `http://127.0.0.1:8000/stocks` for interactive 7-day, 30-day, 90-day, and one-year price charts.
Open `http://127.0.0.1:8000/ideas` for the simplified Suggested Trades experience.
Open `http://127.0.0.1:8000/subscriptions` to total recurring costs and track renewal warnings.
Open `http://127.0.0.1:8000/calendar` for paydays, expenses, and AI-generated money actions.
The Money, Goals, Subscriptions, and Calendar pages save prototype data in the browser. The
AI Coach sends the structured profile to the planning endpoint and keeps plan history locally.

Copy `.env.example` to `.env` and add private NVIDIA and Alpaca credentials. Never commit `.env`.
