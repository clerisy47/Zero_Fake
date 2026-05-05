from __future__ import annotations

from fastapi import FastAPI

from app.models import DecisionResult, HealthResponse, KycSubmission
from app.pipeline import FraudPipeline


pipeline = FraudPipeline()
app = FastAPI(title="KYC Fraud Detection Pipeline", version="1.0.0")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/kyc/submit", response_model=DecisionResult)
def submit_kyc(submission: KycSubmission) -> DecisionResult:
    return pipeline.process(submission)
