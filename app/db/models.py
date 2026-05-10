from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class MongoDBBase(BaseModel):
    """Base model for MongoDB documents."""
    
    id: Optional[str] = Field(None, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True


class KycSubmissionDocument(MongoDBBase):
    """MongoDB document for storing KYC submissions."""
    
    submission_id: str = Field(..., unique=True, index=True)
    channel: str
    claimed_country: str
    
    # Gateway data
    gateway_tls_valid: bool
    gateway_ip_requests_last_minute: int
    gateway_device_requests_last_minute: int
    gateway_session_token_valid: bool
    
    # Device data
    device_fingerprint: str = Field(..., index=True)
    device_user_agent: str
    device_known_recent_submissions: int
    
    # Network data
    network_ip: str = Field(..., index=True)
    network_is_vpn: bool
    network_is_tor: bool
    network_country: str
    
    # Document data
    document_type: str
    document_number: str = Field(..., index=True)
    document_full_name: str = Field(..., index=True)
    document_dob: str
    document_nepal_district: Optional[str] = None
    
    # Biometric data (base64 encoded images stored separately)
    biometric_liveness_score: float
    biometric_face_similarity_score: float
    biometric_deepfake_score: float
    biometric_camera_injection_detected: bool
    
    # Document images (file references)
    document_image_id: Optional[str] = None
    biometric_image_id: Optional[str] = None
    
    # Decision data
    decision: str
    risk_score: float
    risk_breakdown: Dict[str, float]
    hard_fail: Optional[Dict[str, str]] = None
    reason_codes: List[str]
    
    # Processing
    processing_time_ms: int
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Status
    status: str = Field(default="pending")  # pending, approved, rejected, manual_review, step_up
    analyst_notes: Optional[str] = None
    analyst_verdict: Optional[str] = None
    analyst_confidence: Optional[float] = None


class FeedbackVerdictDocument(MongoDBBase):
    """MongoDB document for analyst verdicts."""
    
    submission_id: str = Field(..., index=True)
    analyst_id: str = Field(..., index=True)
    verdict_decision: str
    analyst_confidence: float
    notes: Optional[str] = None
    is_correct: Optional[bool] = None  # Set after validation
    corrected_at: Optional[datetime] = None
    
    # Versioning
    verdict_version: int = Field(default=1)


class UserDocument(MongoDBBase):
    """MongoDB document for system users."""
    
    username: str = Field(..., unique=True, index=True)
    email: str = Field(..., unique=True, index=True)
    hashed_password: str
    role: str = Field(default="analyst")  # analyst, admin, reviewer
    is_active: bool = Field(default=True)
    organization: Optional[str] = None
    
    # Tracking
    last_login: Optional[datetime] = None
    login_attempts: int = Field(default=0)
    locked_until: Optional[datetime] = None


class SessionTokenDocument(MongoDBBase):
    """MongoDB document for session tokens."""
    
    token: str = Field(..., unique=True, index=True)
    user_id: str = Field(..., index=True)
    ip_address: str
    device_fingerprint: str
    expires_at: datetime = Field(..., index=True)
    is_active: bool = Field(default=True)
    
    # Security
    revoked_at: Optional[datetime] = None
    revoke_reason: Optional[str] = None


class RateLimitDocument(MongoDBBase):
    """MongoDB document for rate limiting tracking."""
    
    identifier: str = Field(..., index=True)  # IP or device ID
    identifier_type: str  # "ip" or "device"
    request_count: int = Field(default=1)
    last_request_at: datetime = Field(default_factory=datetime.utcnow)
    window_start: datetime = Field(default_factory=datetime.utcnow)
    is_blocked: bool = Field(default=False)
    blocked_until: Optional[datetime] = None


class ModelTrainingLogDocument(MongoDBBase):
    """MongoDB document for tracking model training sessions."""
    
    training_id: str = Field(..., unique=True, index=True)
    model_version: str
    training_samples_count: int
    training_data_split: Dict[str, float]  # train, val, test percentages
    
    # Results
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    
    # Performance
    training_duration_seconds: Optional[float] = None
    model_size_bytes: Optional[int] = None
    
    # Deployment
    deployed: bool = Field(default=False)
    deployed_at: Optional[datetime] = None
    production: bool = Field(default=False)


class DeduplicationStoreDocument(MongoDBBase):
    """MongoDB document for deduplication store (replaces in-memory store)."""
    
    # Document deduplication
    document_numbers: List[str] = Field(default_factory=list)
    document_hashes: List[str] = Field(default_factory=list)
    
    # Name deduplication
    phonetic_name_keys: List[str] = Field(default_factory=list)
    
    # Face embedding vectors
    face_embeddings: Dict[str, List[float]] = Field(default_factory=dict)  # submission_id -> embedding
    
    # Metadata
    store_version: int = Field(default=1)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    total_entries: int = Field(default=0)
