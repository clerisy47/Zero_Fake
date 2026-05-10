# ZeroFake Quickstart

## 1) Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm install
```

## 2) Start Services

### Backend

```bash
uvicorn app.main:app --reload
```

Backend: `http://127.0.0.1:8000`
Docs: `http://127.0.0.1:8000/docs`

### Frontend

```bash
npm run dev
```

Frontend: `http://127.0.0.1:5173`

## 3) Minimal API Flow

1. Register user via `POST /auth/register`
2. Login via `POST /auth/login`
3. Submit KYC via `POST /kyc/submit`
4. Submit analyst verdict via `POST /feedback/verdict`
5. Trigger retraining (admin) via `POST /admin/retrain`

Use `http://127.0.0.1:8000/docs` for exact payload schemas.

## 4) Verify XGBoost Scorer

```bash
python - <<'PY'
from app.risk import RiskScorer
s = RiskScorer()
print(s.model_metadata)
PY
```

Expected backend metadata includes `backend: gradient_boosting` with XGBoost model usage.
