## Local setup (Cursor IDE)

### Backend (FastAPI)

From project root:

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
cd backend
uvicorn app.main:app --reload
```

Backend runs at `http://localhost:8000`.

### Frontend (React + Vite)

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173` and talks to the backend at `http://localhost:8000`.

### Datasets

The backend auto-loads on startup from `datasets/` **or** (fallback) the project root:

- `oil_dataset.csv`
- `equity_dataset.csv`
- `multi_asset_dataset.csv`
- `macro_dataset.csv`

It normalizes both the required schema and the provided hackathon CSV schemas into:

- Market: `timestamp,ticker,open,high,low,close,volume`
- Macro: `timestamp,interest_rate,inflation,gdp_growth,market_sentiment`

