# Table4
Finance app with Nemotron

## LifePath AI backend

The backend uses Python and FastAPI for deterministic financial calculations. NVIDIA
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
- `GET /api/v1/stocks/{symbol}` returns the latest Alpaca/IEX stock quote.
- `GET /api/v1/stocks/{symbol}/history` returns recent daily price history.
- `GET /api/v1/stocks/{symbol}/insight` calculates recent risk metrics and asks Nemotron to explain them.

Open `http://127.0.0.1:8000/stocks` to use the connected stock lookup page.
The Money and Goals pages save prototype data in the browser, and the AI Coach page sends
that structured profile to the planning endpoint.

Copy `.env.example` to `.env` and add private NVIDIA and Alpaca credentials. Never commit `.env`.
