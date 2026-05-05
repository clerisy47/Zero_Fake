from __future__ import annotations

import math
from typing import Dict, List

from app.models import Decision, DecisionResult, HardFail, KycSubmission, LayerResult, RiskBreakdown


class RiskScorer:
    def __init__(self) -> None:
        self.gbm_weight = 0.7
        self.bio_weight = 0.3
        self.bias = -0.8

    @staticmethod
    def _sigmoid(x: float) -> float:
        return 1.0 / (1.0 + math.exp(-x))

    @staticmethod
    def _logit(p: float) -> float:
        p = min(max(p, 1e-5), 1 - 1e-5)
        return math.log(p / (1.0 - p))

    def _category_scores(self, layer_results: List[LayerResult]) -> Dict[str, float]:
        categories = {
            "gateway": "ingestion_gateway",
            "pre_screen": "pre_screening",
            "document": "document_analysis",
            "biometric": "biometric_verification",
            "dedup": "identity_deduplication",
        }

        by_layer = {lr.layer_name: lr for lr in layer_results}
        result: Dict[str, float] = {}

        for key, layer_name in categories.items():
            layer = by_layer.get(layer_name)
            if not layer or not layer.signals:
                result[key] = 0.0
                continue
            score = sum(s.value_normalized * s.confidence for s in layer.signals)
            denom = sum(s.confidence for s in layer.signals)
            result[key] = (score / denom) * 100.0 if denom > 0 else 0.0

        return result

    def score(self, submission: KycSubmission, layer_results: List[LayerResult]) -> DecisionResult:
        hard_fail = next((lr.hard_fail for lr in layer_results if lr.hard_fail), None)
        category_scores = self._category_scores(layer_results)

        # Approximate GBM probability from tabular signals.
        gbm_base = (
            0.05 * category_scores.get("gateway", 0.0)
            + 0.20 * category_scores.get("pre_screen", 0.0)
            + 0.30 * category_scores.get("document", 0.0)
            + 0.15 * category_scores.get("dedup", 0.0)
        ) / 100.0

        # Auxiliary biometric probability.
        bio_base = category_scores.get("biometric", 0.0) / 100.0

        z = (
            self.gbm_weight * self._logit(gbm_base if gbm_base > 0 else 1e-5)
            + self.bio_weight * self._logit(bio_base if bio_base > 0 else 1e-5)
            + self.bias
        )

        # Add bounded policy terms.
        if category_scores.get("dedup", 0.0) > 75:
            z += 0.8
        if category_scores.get("document", 0.0) > 80:
            z += 0.6
        if category_scores.get("gateway", 0.0) > 70:
            z += 0.5

        blended_score = round(self._sigmoid(z) * 100.0, 2)

        reason_codes = [
            s.reason_code
            for layer in layer_results
            for s in layer.signals
            if s.value_normalized >= 0.6
        ]

        if hard_fail:
            decision = Decision.AUTO_REJECT
            blended_score = max(blended_score, 95.0)
            if hard_fail.reason_code not in reason_codes:
                reason_codes.append(hard_fail.reason_code)
        elif blended_score < 25:
            decision = Decision.AUTO_APPROVE
        elif blended_score < 50:
            decision = Decision.STEP_UP
        elif blended_score < 75:
            decision = Decision.MANUAL_REVIEW
        else:
            decision = Decision.AUTO_REJECT

        return DecisionResult(
            submission_id=submission.submission_id,
            decision=decision,
            risk_score=blended_score,
            hard_fail=hard_fail,
            reason_codes=sorted(set(reason_codes)),
            risk_breakdown=RiskBreakdown(
                category_scores={k: round(v, 2) for k, v in category_scores.items()},
                blended_score=blended_score,
            ),
            layer_results=layer_results,
        )
