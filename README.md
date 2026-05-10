# ZeroFake

ZeroFake is a KYC fraud detection system built for Nepal-focused onboarding flows. It combines layered fraud checks, offline-capable signal extraction, and model-based risk decisions with analyst feedback retraining.

## Current Status

- Eight-stage fraud pipeline is implemented in the backend
- XGBoost is the active risk model backend (no logistic scoring path)
- Hard-fail rules are enforced for critical fraud conditions
- Analyst feedback is captured and used for retraining
- Admin retraining deploys only non-regressing candidate models

## Pipeline Overview

1. Intake gateway
2. Pre-screening
3. Document analysis
4. Biometric checks
5. Identity deduplication
6. XGBoost risk scoring
7. Decision routing
8. Feedback loop and retraining

## Risk Scoring Details

- Runtime model: `xgboost.XGBClassifier`
- Cold start: bootstrap-trained XGBoost model in memory
- Persisted model path: `models/risk_gbm.joblib`
- Retraining source:
  - `kyc_submissions.category_scores`
  - `feedback_verdicts.verdict_decision`
- Deployment gate:
  - Candidate is deployed only when validation AUC and validation accuracy are both not worse than the currently loaded model on the same validation split

## Project Layout

```text
Zero_Fake/
  app/
    main.py
    pipeline.py
    engines.py
    risk.py
    feedback.py
    models.py
    db/
    ml_models/
    security/
  src/
  tests/
  QUICKSTART.md
  TECH_STACK.md
  requirements.txt
```

## Backend Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend URL: `http://127.0.0.1:8000`
API docs: `http://127.0.0.1:8000/docs`

## Frontend Setup

```bash
npm install
npm run dev
```

Frontend URL: `http://127.0.0.1:5173`

## Main API Endpoints

- `GET /health`
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/logout`
- `POST /kyc/submit`
- `POST /feedback/verdict`
- `GET /feedback/stats`
- `POST /admin/retrain`
- `GET /admin/submissions`
- `GET /admin/users`

## Model Retraining Flow

1. A submission is scored and stored with category-level scores.
2. Analyst verdicts are collected.
3. Admin triggers retraining through `POST /admin/retrain`.
4. A candidate XGBoost model is trained.
5. Candidate is deployed only if it passes the non-regression gate.
6. Training metadata is stored in `model_training_logs`.

## Notes

- If `models/risk_gbm.joblib` is absent, the scorer auto-bootstraps an XGBoost model.
- `tests/test_pipeline.py` currently has fixture drift for required `DeviceInput` fields and needs a separate test data update.
