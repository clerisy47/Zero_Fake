"""Database Module - MongoDB configuration and models."""

from app.db.config import Database, Settings, get_database, settings
from app.db.models import (
    KycSubmissionDocument,
    FeedbackVerdictDocument,
    UserDocument,
    SessionTokenDocument,
    RateLimitDocument,
    ModelTrainingLogDocument,
    DeduplicationStoreDocument,
)

__all__ = [
    "Database",
    "Settings",
    "get_database",
    "settings",
    "KycSubmissionDocument",
    "FeedbackVerdictDocument",
    "UserDocument",
    "SessionTokenDocument",
    "RateLimitDocument",
    "ModelTrainingLogDocument",
    "DeduplicationStoreDocument",
]
