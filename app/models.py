from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class Decision(str, Enum):
    AUTO_APPROVE = "auto_approve"
    MANUAL_REVIEW = "manual_review"
    AUTO_REJECT = "auto_reject"
    STEP_UP = "step_up_verification"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Signal(BaseModel):
    signal_name: str
    value_raw: str
    value_normalized: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    reason_code: str
    latency_ms: int = Field(ge=0)
    version: str = "v1"
    severity: Severity


class HardFail(BaseModel):
    reason_code: str
    reason: str


class GatewayInput(BaseModel):
    tls_valid: bool
    ip_requests_last_minute: int = Field(ge=0)
    device_requests_last_minute: int = Field(ge=0)
    session_token_valid: bool


class DeviceInput(BaseModel):
    canvas_fingerprint_hash: str
    installed_font_count: int
    user_agent: str
    accelerometer_variance: float
    webgl_renderer_hash: str
    device_id: str
    known_recent_submission_count: int = Field(ge=0)
    os_family: str


class NetworkInput(BaseModel):
    ip: str
    is_vpn: bool
    is_tor: bool
    is_datacenter_proxy: bool
    country: str
    asn_type: str


class BehaviorInput(BaseModel):
    form_completion_seconds: float = Field(ge=0)
    copy_paste_events: int = Field(ge=0)
    typing_interval_stddev_ms: float = Field(ge=0)
    mouse_path_entropy: float = Field(ge=0)


class DocumentInput(BaseModel):
    document_type: str
    issuing_country: str
    document_number: str
    full_name: str
    dob: str
    claimed_age: int = Field(ge=0, le=120)
    expiry: str
    ela_score: float = Field(ge=0.0, le=1.0)
    font_match_score: float = Field(ge=0.0, le=1.0)
    mrz_checksum_valid: bool
    template_match_score: float = Field(ge=0.0, le=1.0)
    image_quality_score: float = Field(ge=0.0, le=1.0)
    ocr_field_validation: float = Field(ge=0.0, le=1.0, default=1.0)
    hologram_confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    nepal_district: Optional[str] = None


class BiometricInput(BaseModel):
    liveness_score: float = Field(ge=0.0, le=1.0)
    face_similarity_score: float = Field(ge=0.0, le=1.0)
    face_embedding: List[float] = Field(default_factory=list)
    deepfake_score: float = Field(ge=0.0, le=1.0)
    camera_injection_detected: bool
    estimated_age: int = Field(ge=0, le=120)


class KycSubmission(BaseModel):
    submission_id: str
    channel: str
    claimed_country: str
    gateway: GatewayInput
    device: DeviceInput
    network: NetworkInput
    behavior: BehaviorInput
    document: DocumentInput
    biometric: BiometricInput
    timestamp: Optional[datetime] = None


class LayerResult(BaseModel):
    layer_name: str
    signals: List[Signal]
    hard_fail: Optional[HardFail] = None


class RiskBreakdown(BaseModel):
    category_scores: Dict[str, float]
    blended_score: float = Field(ge=0.0, le=100.0)


class DecisionResult(BaseModel):
    submission_id: str
    decision: Decision
    risk_score: float = Field(ge=0.0, le=100.0)
    hard_fail: Optional[HardFail] = None
    reason_codes: List[str]
    risk_breakdown: RiskBreakdown
    layer_results: List[LayerResult]
    processing_time_ms: int = 0


class HealthResponse(BaseModel):
    status: str


class AnalystVerdict(BaseModel):
    submission_id: str
    verdict_decision: Decision
    analyst_confidence: float = Field(ge=0.0, le=1.0)
    notes: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
