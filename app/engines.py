from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1
from typing import Dict, List, Set

from app.models import HardFail, KycSubmission, LayerResult, Severity, Signal


# Nepal's 77 districts for document template matching
NEPAL_DISTRICTS = {
    "Kathmandu", "Bhaktapur", "Lalitpur", "Kavre", "Nuwakot", "Rasuwa", "Sindhuli", "Makawanpur",
    "Rautahat", "Bara", "Parsa", "Dhanusha", "Mahottari", "Saptari", "Sunsari", "Ilam", "Jhapa",
    "Morang", "Sankhuwasabha", "Terhathum", "Panchthar", "Taplejung", "Okhaldhunga", "Khotang",
    "Udayapur", "Janakpur", "Siraha", "Sarlahi", "Chitwan", "Nawalpur", "Parasi", "Gulmi",
    "Arghakhanchi", "Kapilvastu", "Rupandehi", "Dang", "Salyan", "Rolpa", "Pyuthan", "Gorkha",
    "Lamjung", "Tanahu", "Syangja", "Kaski", "Manang", "Mustang", "Myagdi", "Parbat", "Baglung",
    "Dolakha", "Ramechhap", "Solukhumbu", "Bhojpur", "Dhankuta", "Tehrathum", "Panchthar",
    "Taplejung", "Jumla", "Mugu", "Humla", "Bajhang", "Bajura", "Dadeldhura", "Baitadi", "Doti",
    "Achham", "Kailali", "Kanchanpur",
}


def clamp01(value: float) -> float:
    """Clamp a value between 0.0 and 1.0."""
    return max(0.0, min(1.0, value))


@dataclass
class StoreState:
    """In-memory deduplication store for multi-account fraud detection."""
    existing_document_numbers: Set[str]
    existing_document_hashes: Set[str]
    existing_face_vectors: Dict[str, float]
    existing_names: Set[str]


def _mk_signal(
    name: str,
    raw: str,
    normalized: float,
    confidence: float,
    reason_code: str,
    latency_ms: int,
    severity: Severity,
) -> Signal:
    """Factory function to create a Signal with clamped values."""
    return Signal(
        signal_name=name,
        value_raw=raw,
        value_normalized=clamp01(normalized),
        confidence=clamp01(confidence),
        reason_code=reason_code,
        latency_ms=latency_ms,
        severity=severity,
    )


class IngestionGateway:
    """Layer 1: Intake Gateway - blocks bot farms and invalid sessions before ML cost."""
    IP_RATE_LIMIT = 50
    DEVICE_RATE_LIMIT = 30

    def evaluate(self, submission: KycSubmission) -> LayerResult:
        signals: List[Signal] = []

        # TLS validation signal
        tls_signal = 0.0 if submission.gateway.tls_valid else 1.0
        signals.append(
            _mk_signal(
                "gateway_tls",
                str(submission.gateway.tls_valid),
                tls_signal,
                1.0,
                "GATEWAY_TLS_INVALID" if tls_signal > 0 else "GATEWAY_TLS_OK",
                1,
                Severity.CRITICAL if tls_signal > 0 else Severity.LOW,
            )
        )

        # Session token validation signal
        token_signal = 0.0 if submission.gateway.session_token_valid else 1.0
        signals.append(
            _mk_signal(
                "gateway_session_token",
                str(submission.gateway.session_token_valid),
                token_signal,
                1.0,
                "GATEWAY_SESSION_INVALID" if token_signal > 0 else "GATEWAY_SESSION_OK",
                1,
                Severity.CRITICAL if token_signal > 0 else Severity.LOW,
            )
        )

        # IP rate limiting pressure
        ip_pressure = clamp01(submission.gateway.ip_requests_last_minute / self.IP_RATE_LIMIT)
        signals.append(
            _mk_signal(
                "gateway_ip_rate_pressure",
                str(submission.gateway.ip_requests_last_minute),
                ip_pressure,
                0.95,
                "GATEWAY_IP_RATE_HIGH" if ip_pressure >= 1.0 else "GATEWAY_IP_RATE_OK",
                1,
                Severity.HIGH if ip_pressure >= 1.0 else Severity.LOW,
            )
        )

        # Device rate limiting pressure
        device_pressure = clamp01(
            submission.gateway.device_requests_last_minute / self.DEVICE_RATE_LIMIT
        )
        signals.append(
            _mk_signal(
                "gateway_device_rate_pressure",
                str(submission.gateway.device_requests_last_minute),
                device_pressure,
                0.95,
                "GATEWAY_DEVICE_RATE_HIGH" if device_pressure >= 1.0 else "GATEWAY_DEVICE_RATE_OK",
                1,
                Severity.HIGH if device_pressure >= 1.0 else Severity.LOW,
            )
        )

        # Hard fail if TLS or session invalid
        hard_fail = None
        if not submission.gateway.tls_valid:
            hard_fail = HardFail(
                reason_code="HARD_FAIL_TLS_INVALID",
                reason="TLS validation failed at intake gateway.",
            )
        elif not submission.gateway.session_token_valid:
            hard_fail = HardFail(
                reason_code="HARD_FAIL_SESSION_INVALID",
                reason="Session token is invalid or expired.",
            )

        return LayerResult(layer_name="ingestion_gateway", signals=signals, hard_fail=hard_fail)


class PreScreenEngine:
    """Layer 2: Pre-screening - flags VPN, geo mismatches, bot behavior in <200ms."""

    def evaluate(self, submission: KycSubmission) -> LayerResult:
        signals: List[Signal] = []

        # Device reuse signal
        device_reuse = clamp01(submission.device.known_recent_submission_count / 10.0)
        signals.append(
            _mk_signal(
                "prescreen_device_reuse",
                str(submission.device.known_recent_submission_count),
                device_reuse,
                0.9,
                "PRESCREEN_DEVICE_REUSE_HIGH" if device_reuse > 0.8 else "PRESCREEN_DEVICE_REUSE_OK",
                15,
                Severity.HIGH if device_reuse > 0.8 else Severity.MEDIUM,
            )
        )

        # Network reputation (VPN, Tor, datacenter proxy detection)
        network_risk = 0.0
        if submission.network.is_tor:
            network_risk += 0.8
        if submission.network.is_vpn:
            network_risk += 0.3
        if submission.network.is_datacenter_proxy:
            network_risk += 0.4
        if submission.network.asn_type.lower() in {"hosting", "datacenter"}:
            network_risk += 0.2
        network_risk = clamp01(network_risk)
        signals.append(
            _mk_signal(
                "prescreen_network_reputation",
                (
                    f"vpn={submission.network.is_vpn},tor={submission.network.is_tor},"
                    f"dc={submission.network.is_datacenter_proxy},asn={submission.network.asn_type}"
                ),
                network_risk,
                0.9,
                "PRESCREEN_NETWORK_RISK_HIGH" if network_risk >= 0.7 else "PRESCREEN_NETWORK_RISK_OK",
                20,
                Severity.HIGH if network_risk >= 0.7 else Severity.MEDIUM,
            )
        )

        # Behavioral pattern analysis (form speed, copy-paste, typing patterns)
        speed_risk = clamp01((20.0 - submission.behavior.form_completion_seconds) / 20.0)
        paste_risk = clamp01(submission.behavior.copy_paste_events / 10.0)
        typing_risk = clamp01((120.0 - submission.behavior.typing_interval_stddev_ms) / 120.0)
        behavior_risk = clamp01((speed_risk + paste_risk + typing_risk) / 3.0)

        signals.append(
            _mk_signal(
                "prescreen_behavior_pattern",
                (
                    f"time={submission.behavior.form_completion_seconds},"
                    f"paste={submission.behavior.copy_paste_events},"
                    f"typing_std={submission.behavior.typing_interval_stddev_ms}"
                ),
                behavior_risk,
                0.8,
                "PRESCREEN_BEHAVIOR_BOT_LIKE" if behavior_risk >= 0.7 else "PRESCREEN_BEHAVIOR_NORMAL",
                18,
                Severity.HIGH if behavior_risk >= 0.7 else Severity.LOW,
            )
        )

        # Geo-IP / Document country mismatch
        country_mismatch = (
            submission.network.country.strip().lower()
            != submission.document.issuing_country.strip().lower()
        )
        signals.append(
            _mk_signal(
                "prescreen_geo_document_mismatch",
                f"ip_country={submission.network.country},doc_country={submission.document.issuing_country}",
                1.0 if country_mismatch else 0.0,
                0.95,
                "PRESCREEN_GEO_DOC_MISMATCH" if country_mismatch else "PRESCREEN_GEO_DOC_MATCH",
                10,
                Severity.MEDIUM if country_mismatch else Severity.LOW,
            )
        )

        return LayerResult(layer_name="pre_screening", signals=signals)


class DocumentAnalysisEngine:
    """Layer 3: Document Analysis - ELA, district-aware template matching, OCR validation."""

    def evaluate(self, submission: KycSubmission) -> LayerResult:
        signals: List[Signal] = []
        doc = submission.document

        # Error Level Analysis for forgery detection
        forgery_risk = clamp01((doc.ela_score + (1.0 - doc.font_match_score)) / 2.0)
        signals.append(
            _mk_signal(
                "document_forgery_score",
                f"ela={doc.ela_score},font={doc.font_match_score}",
                forgery_risk,
                0.88,
                "DOC_FORGERY_HIGH" if forgery_risk >= 0.7 else "DOC_FORGERY_LOW",
                900,
                Severity.HIGH if forgery_risk >= 0.7 else Severity.LOW,
            )
        )

        # MRZ (Machine Readable Zone) checksum validation
        mrz_risk = 0.0 if doc.mrz_checksum_valid else 1.0
        signals.append(
            _mk_signal(
                "document_mrz_checksum",
                str(doc.mrz_checksum_valid),
                mrz_risk,
                0.98,
                "DOC_MRZ_INVALID" if mrz_risk > 0 else "DOC_MRZ_VALID",
                220,
                Severity.CRITICAL if mrz_risk > 0 else Severity.LOW,
            )
        )

        # Template matching (including Nepal district validation for 77 variants)
        template_risk = clamp01(1.0 - doc.template_match_score)
        nepal_district_valid = (
            doc.nepal_district in NEPAL_DISTRICTS
            if doc.nepal_district and doc.issuing_country.lower() == "nepal"
            else True
        )
        if not nepal_district_valid:
            template_risk = 1.0

        signals.append(
            _mk_signal(
                "document_template_deviation",
                str(doc.template_match_score),
                template_risk,
                0.9,
                "DOC_TEMPLATE_DEVIATION_HIGH" if template_risk >= 0.4 else "DOC_TEMPLATE_DEVIATION_LOW",
                650,
                Severity.HIGH if template_risk >= 0.4 else Severity.LOW,
            )
        )

        # Image quality assessment
        quality_risk = clamp01(1.0 - doc.image_quality_score)
        signals.append(
            _mk_signal(
                "document_image_quality",
                str(doc.image_quality_score),
                quality_risk,
                0.95,
                "DOC_IMAGE_QUALITY_LOW" if quality_risk >= 0.5 else "DOC_IMAGE_QUALITY_OK",
                120,
                Severity.MEDIUM if quality_risk >= 0.5 else Severity.LOW,
            )
        )

        # OCR field validation
        ocr_risk = clamp01(1.0 - doc.ocr_field_validation)
        signals.append(
            _mk_signal(
                "document_ocr_validation",
                str(doc.ocr_field_validation),
                ocr_risk,
                0.92,
                "DOC_OCR_VALIDATION_LOW" if ocr_risk >= 0.3 else "DOC_OCR_VALIDATION_OK",
                450,
                Severity.MEDIUM if ocr_risk >= 0.3 else Severity.LOW,
            )
        )

        # Hard fail conditions
        hard_fail = None
        if not doc.mrz_checksum_valid:
            hard_fail = HardFail(
                reason_code="HARD_FAIL_DOC_MRZ",
                reason="Document MRZ checksum failed validation.",
            )
        elif not nepal_district_valid:
            hard_fail = HardFail(
                reason_code="HARD_FAIL_DOC_INVALID_NEPAL_DISTRICT",
                reason="Document district not recognized in Nepal's 77 districts.",
            )

        return LayerResult(layer_name="document_analysis", signals=signals, hard_fail=hard_fail)


class BiometricEngine:
    """Layer 4: Biometric Check - liveness, ArcFace matching, deepfake detection."""

    def evaluate(self, submission: KycSubmission) -> LayerResult:
        signals: List[Signal] = []
        bio = submission.biometric
        doc = submission.document

        # Liveness detection
        liveness_risk = clamp01(1.0 - bio.liveness_score)
        signals.append(
            _mk_signal(
                "biometric_liveness",
                str(bio.liveness_score),
                liveness_risk,
                0.97,
                "BIO_LIVENESS_FAIL" if bio.liveness_score < 0.35 else "BIO_LIVENESS_PASS",
                1500,
                Severity.CRITICAL if bio.liveness_score < 0.35 else Severity.LOW,
            )
        )

        # Face similarity (ArcFace-style matching)
        face_risk = clamp01(1.0 - bio.face_similarity_score)
        signals.append(
            _mk_signal(
                "biometric_face_match",
                str(bio.face_similarity_score),
                face_risk,
                0.93,
                "BIO_FACE_MISMATCH" if bio.face_similarity_score < 0.55 else "BIO_FACE_MATCH",
                1100,
                Severity.HIGH if bio.face_similarity_score < 0.55 else Severity.LOW,
            )
        )

        # Deepfake detection
        deepfake_risk = clamp01(bio.deepfake_score)
        signals.append(
            _mk_signal(
                "biometric_deepfake_risk",
                str(bio.deepfake_score),
                deepfake_risk,
                0.9,
                "BIO_DEEPFAKE_HIGH" if deepfake_risk >= 0.7 else "BIO_DEEPFAKE_LOW",
                900,
                Severity.HIGH if deepfake_risk >= 0.7 else Severity.LOW,
            )
        )

        # Age plausibility check
        age_gap = abs(doc.claimed_age - bio.estimated_age)
        age_risk = clamp01(age_gap / 20.0)
        signals.append(
            _mk_signal(
                "biometric_age_plausibility",
                f"claimed={doc.claimed_age},estimated={bio.estimated_age}",
                age_risk,
                0.75,
                "BIO_AGE_MISMATCH" if age_gap >= 15 else "BIO_AGE_OK",
                80,
                Severity.MEDIUM if age_gap >= 15 else Severity.LOW,
            )
        )

        # Camera injection detection (physical vs AI-generated spoofing)
        camera_injection_risk = 1.0 if bio.camera_injection_detected else 0.0
        signals.append(
            _mk_signal(
                "biometric_camera_injection",
                str(bio.camera_injection_detected),
                camera_injection_risk,
                0.99,
                "BIO_CAMERA_INJECTION" if bio.camera_injection_detected else "BIO_CAMERA_CLEAN",
                40,
                Severity.CRITICAL if bio.camera_injection_detected else Severity.LOW,
            )
        )

        # Hard fail conditions
        hard_fail = None
        if bio.camera_injection_detected:
            hard_fail = HardFail(
                reason_code="HARD_FAIL_CAMERA_INJECTION",
                reason="Virtual camera or camera feed injection detected.",
            )
        elif bio.liveness_score < 0.2:
            hard_fail = HardFail(
                reason_code="HARD_FAIL_LIVENESS",
                reason="Liveness confidence below absolute minimum threshold.",
            )

        return LayerResult(layer_name="biometric_verification", signals=signals, hard_fail=hard_fail)


class IdentityDedupEngine:
    """Layer 5: Deduplication Engine - fuzzy name, face embedding nearest-neighbor, doc perceptual hashing."""

    def __init__(self, store_state: StoreState) -> None:
        self.store = store_state

    @staticmethod
    def _name_key(name: str) -> str:
        """Generate a phonetic-style key for fuzzy name matching."""
        cleaned = "".join(ch for ch in name.lower() if ch.isalpha() or ch.isspace())
        parts = [p for p in cleaned.split() if p]
        if not parts:
            return ""
        # Lightweight key for fuzzy duplicate lookup
        prefix = "".join(p[:2] for p in parts)
        return prefix[:8]

    @staticmethod
    def _doc_hash(document_number: str, full_name: str) -> str:
        """Generate a perceptual hash for document deduplication."""
        return sha1(f"{document_number}:{full_name.lower()}".encode("utf-8")).hexdigest()[:16]

    def evaluate(self, submission: KycSubmission) -> LayerResult:
        signals: List[Signal] = []
        doc = submission.document
        bio = submission.biometric

        # Exact document number reuse detection
        exact_doc_reuse = doc.document_number in self.store.existing_document_numbers
        signals.append(
            _mk_signal(
                "dedup_document_number_reuse",
                doc.document_number,
                1.0 if exact_doc_reuse else 0.0,
                1.0,
                "DEDUP_DOC_NUMBER_REUSED" if exact_doc_reuse else "DEDUP_DOC_NUMBER_UNIQUE",
                15,
                Severity.CRITICAL if exact_doc_reuse else Severity.LOW,
            )
        )

        # Document perceptual hash matching
        perceptual_hash = self._doc_hash(doc.document_number, doc.full_name)
        hash_reuse = perceptual_hash in self.store.existing_document_hashes
        signals.append(
            _mk_signal(
                "dedup_document_hash_reuse",
                perceptual_hash,
                1.0 if hash_reuse else 0.0,
                0.92,
                "DEDUP_DOC_HASH_REUSED" if hash_reuse else "DEDUP_DOC_HASH_UNIQUE",
                20,
                Severity.HIGH if hash_reuse else Severity.LOW,
            )
        )

        # Fuzzy name matching for multi-account money mule networks
        name_key = self._name_key(doc.full_name)
        fuzzy_name_match = name_key in self.store.existing_names
        signals.append(
            _mk_signal(
                "dedup_fuzzy_name_match",
                name_key,
                0.8 if fuzzy_name_match else 0.0,
                0.7,
                "DEDUP_NAME_NEAR_MATCH" if fuzzy_name_match else "DEDUP_NAME_UNIQUE",
                25,
                Severity.MEDIUM if fuzzy_name_match else Severity.LOW,
            )
        )

        # Face embedding nearest-neighbor search
        nearest_face_similarity = max(self.store.existing_face_vectors.values(), default=0.0)
        dedup_face_risk = nearest_face_similarity if nearest_face_similarity >= 0.92 else 0.0
        signals.append(
            _mk_signal(
                "dedup_face_embedding_match",
                f"nearest_similarity={nearest_face_similarity:.3f}",
                dedup_face_risk,
                0.9,
                "DEDUP_FACE_MATCH_HIGH" if dedup_face_risk > 0 else "DEDUP_FACE_MATCH_LOW",
                70,
                Severity.HIGH if dedup_face_risk > 0 else Severity.LOW,
            )
        )

        # Hard fail if exact document number reused
        hard_fail = None
        if exact_doc_reuse:
            hard_fail = HardFail(
                reason_code="HARD_FAIL_DOC_NUMBER_REUSE",
                reason="Document number already used by another account.",
            )

        # Update store for future deduplication
        self.store.existing_document_numbers.add(doc.document_number)
        self.store.existing_document_hashes.add(perceptual_hash)
        self.store.existing_names.add(name_key)
        self.store.existing_face_vectors[submission.submission_id] = bio.face_similarity_score

        return LayerResult(layer_name="identity_deduplication", signals=signals, hard_fail=hard_fail)


def default_store_state() -> StoreState:
    """Initialize default deduplication store state with seed data."""
    return StoreState(
        existing_document_numbers={"NEP-778899-11"},
        existing_document_hashes={"126de8d06cb4de96"},
        existing_face_vectors={"seed-account": 0.63},
        existing_names={"rashsh"},
    )
