from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from app.models import AnalystVerdict, Decision, KycSubmission


class FeedbackCollector:
    """Collects analyst verdicts for continuous model retraining."""

    def __init__(self, storage_path: str = "feedback_data") -> None:
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.verdicts_file = self.storage_path / "verdicts.jsonl"

    def record_verdict(self, verdict: AnalystVerdict) -> None:
        """Record an analyst's verdict for a submission."""
        with open(self.verdicts_file, "a") as f:
            f.write(verdict.model_dump_json() + "\n")

    def get_verdicts_since(self, hours: int = 168) -> List[AnalystVerdict]:
        """Get all verdicts from the last N hours (default: 1 week)."""
        if not self.verdicts_file.exists():
            return []

        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        verdicts: List[AnalystVerdict] = []

        with open(self.verdicts_file, "r") as f:
            for line in f:
                if not line.strip():
                    continue
                data = json.loads(line)
                verdict = AnalystVerdict(**data)
                if verdict.timestamp >= cutoff_time:
                    verdicts.append(verdict)

        return verdicts

    def get_verdicts_by_decision(self, decision: Decision) -> List[AnalystVerdict]:
        """Get all verdicts for a specific decision outcome."""
        if not self.verdicts_file.exists():
            return []

        verdicts: List[AnalystVerdict] = []
        with open(self.verdicts_file, "r") as f:
            for line in f:
                if not line.strip():
                    continue
                data = json.loads(line)
                verdict = AnalystVerdict(**data)
                if verdict.verdict_decision == decision:
                    verdicts.append(verdict)

        return verdicts


class ModelRetrainingScheduler:
    """Manages periodic model retraining based on analyst feedback."""

    def __init__(self, feedback_collector: FeedbackCollector) -> None:
        self.feedback_collector = feedback_collector
        self.last_retrain_time: Optional[datetime] = None
        self.retraining_threshold_verdicts = 100  # Retrain after 100 verdicts

    def should_retrain(self) -> bool:
        """Check if model should be retrained (weekly or threshold-based)."""
        if self.last_retrain_time is None:
            # First time, check if we have enough feedback
            recent_verdicts = self.feedback_collector.get_verdicts_since(hours=168)
            return len(recent_verdicts) >= self.retraining_threshold_verdicts

        # Check if 7 days have passed or we've collected enough new verdicts
        days_since_retrain = (datetime.utcnow() - self.last_retrain_time).days
        if days_since_retrain >= 7:
            return True

        # Check if we've accumulated enough verdicts since last retrain
        recent_verdicts = self.feedback_collector.get_verdicts_since(
            hours=int((datetime.utcnow() - self.last_retrain_time).total_seconds() / 3600)
        )
        return len(recent_verdicts) >= self.retraining_threshold_verdicts

    def get_training_data(self) -> tuple[List[dict], List[int]]:
        """
        Extract training data from feedback verdicts.
        Returns: (feature_list, label_list) for model training.
        """
        verdicts = self.feedback_collector.get_verdicts_since(hours=168 * 12)  # Last 12 weeks

        X = []
        y = []

        for verdict in verdicts:
            # Map decision to binary label (1 = reject/fraud, 0 = approve)
            label = 1 if verdict.verdict_decision in {Decision.AUTO_REJECT, Decision.MANUAL_REVIEW} else 0
            # Simple feature: confidence * label weight
            feature = {"analyst_confidence": verdict.analyst_confidence, "verdict_label": label}
            X.append(feature)
            y.append(label)

        return X, y

    def on_retrain_complete(self) -> None:
        """Record that retraining was completed."""
        self.last_retrain_time = datetime.utcnow()
