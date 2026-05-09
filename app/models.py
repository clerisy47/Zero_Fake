from __future__ import annotations

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
    user_agent: str
    os_family: str
    device_id: str
    known_recent_submission_count: int = Field(ge=0)
    user_agent: str
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
    ocr_field_validation: float = Field(ge=0.0, le=1.0)
    hologram_confidence: float = Field(ge=0.0, le=1.0)

    def validate_fields(self):
        # Implement validation checks
        errors = []
        if not re.match(r'^[A-Z0-9]+$', self.document_number):
            errors.append("Document number does not match expected format.")
        if self.expiry < datetime.now():
            errors.append("Expiry date must be in the future.")
        if abs(self.claimed_age - (datetime.now().year - int(self.dob.split('-')[0]))) > 1:
            errors.append("DOB is inconsistent with claimed age.")
        if not fuzzy_match(self.full_name, self.ocr_name):
            errors.append("Name does not match OCR name.")
        self.ocr_field_validation = max(0, 1 - len(errors) * 0.25)
        return errors
    document_type: str
    issuing_country: str
    document_number: str
    full_name: str
    dob: str
    claimed_age: int = Field(ge=0, le=120)
    expiry: str
    ela_score: float = Field(ge=0, le=1)
    font_match_score: float = Field(ge=0, le=1)
    mrz_checksum_valid: bool
    template_match_score: float = Field(ge=0, le=1)
    image_quality_score: float = Field(ge=0, le=1)


class BiometricInput(BaseModel):
    liveness_depth_score: float = Field(ge=0, le=1)
    liveness_texture_score: float = Field(ge=0, le=1)
    liveness_challenge_score: float = Field(ge=0, le=1)
    deepfake_frequency_anomaly_score: float = Field(ge=0, le=1)
    deepfake_boundary_score: float = Field(ge=0, le=1)
    camera_injection_detected: bool
    estimated_age: int = Field(ge=0, le=120)

    def compute_composite_liveness(self):
        return 0.4 * self.liveness_depth_score + 0.35 * self.liveness_texture_score + 0.25 * self.liveness_challenge_score

    def compute_composite_deepfake(self):
        return 0.5 * self.deepfake_frequency_anomaly_score + 0.5 * self.deepfake_boundary_score
    liveness_score: float = Field(ge=0, le=1)
    face_similarity_score: float = Field(ge=0, le=1)
    deepfake_score: float = Field(ge=0, le=1)
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
    # Add new fields with sensible defaults
    ocr_field_validation: float = 1.0
    hologram_confidence: float = 1.0
    liveness_depth_score: float = 0.0
    liveness_texture_score: float = 0.0
    liveness_challenge_score: float = 0.0
    deepfake_frequency_anomaly_score: float = 0.0
    deepfake_boundary_score: float = 0.0
    submission_id: str
    channel: str
    claimed_country: str
    gateway: GatewayInput
    device: DeviceInput
    network: NetworkInput
    behavior: BehaviorInput
    document: DocumentInput
    biometric: BiometricInput


class LayerResult(BaseModel):
    layer_name: str
    signals: List[Signal]
    hard_fail: Optional[HardFail] = None


class RiskBreakdown(BaseModel):
    category_scores: Dict[str, float]
    blended_score: float = Field(ge=0, le=100)


class DecisionResult(BaseModel):
    submission_id: str
    decision: Decision
    risk_score: float = Field(ge=0, le=100)
    hard_fail: Optional[HardFail] = None
    reason_codes: List[str]
    risk_breakdown: RiskBreakdown
    layer_results: List[LayerResult]


class HealthResponse(BaseModel):
    status: str
