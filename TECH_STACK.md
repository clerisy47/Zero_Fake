# ZeroFake Tech Stack

## Backend

- FastAPI + Uvicorn
- Pydantic for schema validation
- MongoDB + Motor for async persistence
- Security: JWT, passlib/bcrypt, request rate limiting

## ML / Risk Engine

- XGBoost (`xgboost.XGBClassifier`) for risk scoring and retraining
- NumPy for numerical features
- scikit-learn utilities:
  - `train_test_split`
  - `roc_auc_score`
- joblib for model persistence (`models/risk_gbm.joblib`)

## Vision / Biometrics

- TensorFlow
- PyTorch
- DeepFace + facenet-pytorch
- OpenCV + MediaPipe
- Tesseract OCR

## Frontend

- React + Vite
- Tailwind CSS

## Runtime Characteristics

- Layered fraud pipeline with hard-fail controls
- XGBoost-based scoring with explicit policy boosts
- Feedback-driven retraining with non-regression deployment gate
