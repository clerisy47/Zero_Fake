from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import joblib
import numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from app.models import Decision, DecisionResult, HardFail, KycSubmission, LayerResult, RiskBreakdown


class RiskScorer:
    FEATURE_ORDER = ["gateway", "pre_screen", "document", "biometric", "dedup"]
    MODEL_PATH = Path("models/risk_gbm.joblib")

    def __init__(self) -> None:
        self.model: XGBClassifier | None = None
        self.model_metadata: Dict[str, float | str] = {"backend": "gradient_boosting"}
        self._load_model()

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

    @classmethod
    def category_scores_to_features(cls, category_scores: Dict[str, float]) -> List[float]:
        """Build a deterministic feature vector from category scores."""
        base = [float(category_scores.get(name, 0.0)) for name in cls.FEATURE_ORDER]
        mean_score = sum(base) / len(base)
        max_score = max(base)
        doc_dedup_interaction = (base[2] * base[4]) / 100.0
        gateway_network_interaction = (base[0] * base[1]) / 100.0
        return [*base, mean_score, max_score, doc_dedup_interaction, gateway_network_interaction]

    def _load_model(self) -> None:
        """Load trained GBM model if available."""
        if not self.MODEL_PATH.exists():
            self._train_bootstrap_model()
            return

        try:
            payload = joblib.load(self.MODEL_PATH)
            model = payload.get("model")
            metadata = payload.get("metadata", {})
            if model is None:
                self._train_bootstrap_model()
                return
            self.model = model
            self.model_metadata = {
                "backend": "gradient_boosting",
                "version": metadata.get("version", "unknown"),
                "validation_accuracy": metadata.get("validation_accuracy"),
                "validation_auc": metadata.get("validation_auc"),
            }
        except Exception:
            # If loading fails, build a bootstrap GBM so inference remains GBM-based.
            self._train_bootstrap_model()

    def _train_bootstrap_model(self) -> None:
        """Train a baseline GBM from rule-based synthetic samples for cold start."""
        rng = np.random.default_rng(42)
        n = 1800
        # Generate synthetic category scores in [0, 100].
        synthetic = rng.uniform(0.0, 100.0, size=(n, len(self.FEATURE_ORDER)))

        feature_rows: List[List[float]] = []
        labels: List[int] = []
        for row in synthetic:
            category = {
                "gateway": float(row[0]),
                "pre_screen": float(row[1]),
                "document": float(row[2]),
                "biometric": float(row[3]),
                "dedup": float(row[4]),
            }

            weighted = (
                0.06 * category["gateway"]
                + 0.20 * category["pre_screen"]
                + 0.30 * category["document"]
                + 0.16 * category["biometric"]
                + 0.28 * category["dedup"]
            )

            if category["dedup"] > 75:
                weighted += 8.0
            if category["document"] > 80:
                weighted += 6.0
            if category["gateway"] > 70:
                weighted += 5.0

            label = 1 if weighted >= 50.0 else 0
            feature_rows.append(self.category_scores_to_features(category))
            labels.append(label)

        model = XGBClassifier(
            objective="binary:logistic",
            n_estimators=200,
            learning_rate=0.05,
            max_depth=4,
            subsample=0.9,
            colsample_bytree=0.9,
            reg_lambda=1.0,
            random_state=42,
            eval_metric="logloss",
            n_jobs=2,
            tree_method="hist",
        )
        model.fit(np.array(feature_rows, dtype=float), np.array(labels, dtype=int))

        self.model = model
        self.model_metadata = {
            "backend": "gradient_boosting",
            "version": "gbm-bootstrap-v1",
        }

    @staticmethod
    def _safe_auc(model: XGBClassifier, X_val: np.ndarray, y_val: np.ndarray) -> float:
        """Compute AUC safely when validation split has a single class."""
        if len(np.unique(y_val)) < 2:
            return 0.5
        probs = model.predict_proba(X_val)[:, 1]
        return float(roc_auc_score(y_val, probs))

    def train_gradient_boosting(self, X_features: List[List[float]], y_labels: List[int]) -> Dict[str, float | str]:
        """Train, validate, and persist a gradient boosting risk model."""
        if len(X_features) < 30:
            raise ValueError("At least 30 labeled samples are required for GBM training.")
        if len(set(y_labels)) < 2:
            raise ValueError("Training data must include both fraud and non-fraud labels.")

        X = np.array(X_features, dtype=float)
        y = np.array(y_labels, dtype=int)

        X_train, X_val, y_train, y_val = train_test_split(
            X,
            y,
            test_size=0.2,
            random_state=42,
            stratify=y,
        )

        model = XGBClassifier(
            objective="binary:logistic",
            n_estimators=300,
            learning_rate=0.05,
            max_depth=4,
            min_child_weight=2,
            subsample=0.9,
            colsample_bytree=0.9,
            reg_lambda=1.0,
            random_state=42,
            eval_metric="logloss",
            n_jobs=2,
            tree_method="hist",
        )
        model.fit(X_train, y_train)

        val_accuracy = float(model.score(X_val, y_val))
        val_auc = self._safe_auc(model, X_val, y_val)

        current_accuracy = 0.0
        current_auc = 0.0
        if self.model is not None:
            current_accuracy = float(self.model.score(X_val, y_val))
            current_auc = self._safe_auc(self.model, X_val, y_val)

        # Deploy only if candidate is not worse on both key metrics.
        should_deploy = self.model is None or (
            val_auc >= current_auc and val_accuracy >= current_accuracy
        )

        metadata: Dict[str, float | str] = {
            "version": "gbm-v1",
            "validation_accuracy": round(val_accuracy, 4),
            "validation_auc": round(val_auc, 4),
            "samples": float(len(X_features)),
            "deployed": "true" if should_deploy else "false",
            "previous_validation_accuracy": round(current_accuracy, 4),
            "previous_validation_auc": round(current_auc, 4),
        }

        if not should_deploy:
            self.model_metadata = {
                "backend": "gradient_boosting",
                "version": self.model_metadata.get("version", "gbm-bootstrap-v1"),
                "validation_accuracy": self.model_metadata.get("validation_accuracy"),
                "validation_auc": self.model_metadata.get("validation_auc"),
                "candidate_validation_accuracy": metadata["validation_accuracy"],
                "candidate_validation_auc": metadata["validation_auc"],
                "deployed": "false",
            }
            return self.model_metadata

        self.MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"model": model, "metadata": metadata}, self.MODEL_PATH)

        self.model = model
        self.model_metadata = {
            "backend": "gradient_boosting",
            "version": metadata["version"],
            "validation_accuracy": metadata["validation_accuracy"],
            "validation_auc": metadata["validation_auc"],
            "deployed": "true",
        }
        return self.model_metadata

    def _gbm_score(self, category_scores: Dict[str, float]) -> float:
        """Predict risk score using trained gradient boosting ensemble."""
        if self.model is None:
            self._train_bootstrap_model()

        features = np.array([self.category_scores_to_features(category_scores)], dtype=float)
        fraud_prob = float(self.model.predict_proba(features)[0][1])

        # Keep explicit policy boosts so regulatory behavior remains predictable.
        risk_score = fraud_prob * 100.0
        if category_scores.get("dedup", 0.0) > 75:
            risk_score += 8.0
        if category_scores.get("document", 0.0) > 80:
            risk_score += 6.0
        if category_scores.get("gateway", 0.0) > 70:
            risk_score += 5.0

        return round(min(100.0, max(0.0, risk_score)), 2)

    def score(self, submission: KycSubmission, layer_results: List[LayerResult]) -> DecisionResult:
        hard_fail = next((lr.hard_fail for lr in layer_results if lr.hard_fail), None)
        category_scores = self._category_scores(layer_results)

        blended_score = self._gbm_score(category_scores)

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
