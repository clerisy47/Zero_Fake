from __future__ import annotations

from app.engines import (
    BiometricEngine,
    DocumentAnalysisEngine,
    IdentityDedupEngine,
    IngestionGateway,
    PreScreenEngine,
    default_store_state,
)
from app.models import DecisionResult, KycSubmission
from app.risk import RiskScorer


class FraudPipeline:
    def __init__(self) -> None:
        self.gateway = IngestionGateway()
        self.pre_screen = PreScreenEngine()
        self.document = DocumentAnalysisEngine()
        self.biometric = BiometricEngine()
        self.dedup = IdentityDedupEngine(default_store_state())
        self.scorer = RiskScorer()

    def process(self, submission: KycSubmission) -> DecisionResult:
        layer_results = [
            self.gateway.evaluate(submission),
            self.pre_screen.evaluate(submission),
            self.document.evaluate(submission),
            self.biometric.evaluate(submission),
            self.dedup.evaluate(submission),
        ]
        return self.scorer.score(submission, layer_results)
