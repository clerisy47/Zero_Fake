from __future__ import annotations

import time

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
    """
    ZeroFake fraud detection pipeline - resolves in under 8 seconds.
    
    Processes KYC submissions through 5 sequential layers:
    1. Ingestion Gateway (<10ms) - TLS, rate limiting
    2. Pre-screening (<200ms) - VPN, geo-IP, behavior
    3. Document Analysis (<1500ms) - ELA, template matching, OCR
    4. Biometric Check (<2000ms) - Liveness, deepfake, face match
    5. Identity Deduplication (<100ms) - Document/name/face dedup
    6. Risk Scoring & Decision Routing (<100ms)
    """

    PIPELINE_TIMEOUT_MS = 8000  # Must complete in under 8 seconds

    def __init__(self) -> None:
        self.gateway = IngestionGateway()
        self.pre_screen = PreScreenEngine()
        self.document = DocumentAnalysisEngine()
        self.biometric = BiometricEngine()
        self.dedup = IdentityDedupEngine(default_store_state())
        self.scorer = RiskScorer()

    def process(self, submission: KycSubmission) -> DecisionResult:
        """Process a KYC submission through all layers and return decision."""
        start_time = time.time()

        # Layer 1: Ingestion Gateway
        gateway_result = self.gateway.evaluate(submission)
        if gateway_result.hard_fail:
            return self._create_result(submission, [gateway_result], time.time() - start_time)

        # Layer 2: Pre-screening
        pre_screen_result = self.pre_screen.evaluate(submission)

        # Layer 3: Document Analysis
        document_result = self.document.evaluate(submission)
        if document_result.hard_fail:
            return self._create_result(
                submission, [gateway_result, pre_screen_result, document_result], time.time() - start_time
            )

        # Layer 4: Biometric Check
        biometric_result = self.biometric.evaluate(submission)
        if biometric_result.hard_fail:
            return self._create_result(
                submission,
                [gateway_result, pre_screen_result, document_result, biometric_result],
                time.time() - start_time,
            )

        # Layer 5: Identity Deduplication
        dedup_result = self.dedup.evaluate(submission)

        # All layers complete, score and decide
        layer_results = [gateway_result, pre_screen_result, document_result, biometric_result, dedup_result]
        return self._create_result(submission, layer_results, time.time() - start_time)

    def _create_result(self, submission: KycSubmission, layer_results: list, elapsed_time: float) -> DecisionResult:
        """Create final decision result with risk scoring."""
        result = self.scorer.score(submission, layer_results)
        # Processing time is set in main.py, but we can track pipeline time here too
        return result

