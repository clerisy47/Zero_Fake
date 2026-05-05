import unittest

from app.models import KycSubmission
from app.pipeline import FraudPipeline


def sample_submission() -> KycSubmission:
    return KycSubmission.model_validate(
        {
            "submission_id": "sub-1001",
            "channel": "mobile_sdk",
            "claimed_country": "Nepal",
            "gateway": {
                "tls_valid": True,
                "ip_requests_last_minute": 8,
                "device_requests_last_minute": 2,
                "session_token_valid": True,
            },
            "device": {
                "device_id": "dev-abc-1",
                "known_recent_submission_count": 1,
                "user_agent": "MobileApp/4.1",
                "os_family": "Android",
            },
            "network": {
                "ip": "203.55.22.12",
                "is_vpn": False,
                "is_tor": False,
                "is_datacenter_proxy": False,
                "country": "Nepal",
                "asn_type": "retail",
            },
            "behavior": {
                "form_completion_seconds": 65,
                "copy_paste_events": 0,
                "typing_interval_stddev_ms": 240,
                "mouse_path_entropy": 0.62,
            },
            "document": {
                "document_type": "passport",
                "issuing_country": "Nepal",
                "document_number": "NEP-331122-10",
                "full_name": "Ramesh Shrestha",
                "dob": "1986-02-15",
                "claimed_age": 40,
                "expiry": "2032-02-15",
                "ela_score": 0.12,
                "font_match_score": 0.92,
                "mrz_checksum_valid": True,
                "template_match_score": 0.91,
                "image_quality_score": 0.89,
            },
            "biometric": {
                "liveness_score": 0.88,
                "face_similarity_score": 0.86,
                "deepfake_score": 0.11,
                "camera_injection_detected": False,
                "estimated_age": 39,
            },
        }
    )


class TestPipeline(unittest.TestCase):
    def setUp(self) -> None:
        self.pipeline = FraudPipeline()

    def test_low_risk_submission_auto_approved_or_step_up(self) -> None:
        result = self.pipeline.process(sample_submission())
        self.assertIn(result.decision.value, {"auto_approve", "step_up_verification"})
        self.assertLess(result.risk_score, 50)

    def test_hard_fail_on_document_reuse(self) -> None:
        bad = sample_submission().model_copy(deep=True)
        bad.submission_id = "sub-1002"
        bad.document.document_number = "NEP-778899-11"

        result = self.pipeline.process(bad)

        self.assertEqual(result.decision.value, "auto_reject")
        self.assertIsNotNone(result.hard_fail)
        self.assertEqual(result.hard_fail.reason_code, "HARD_FAIL_DOC_NUMBER_REUSE")
        self.assertGreaterEqual(result.risk_score, 95)

    def test_hard_fail_on_camera_injection(self) -> None:
        bad = sample_submission().model_copy(deep=True)
        bad.submission_id = "sub-1003"
        bad.biometric.camera_injection_detected = True

        result = self.pipeline.process(bad)

        self.assertEqual(result.decision.value, "auto_reject")
        self.assertIsNotNone(result.hard_fail)
        self.assertEqual(result.hard_fail.reason_code, "HARD_FAIL_CAMERA_INJECTION")


if __name__ == "__main__":
    unittest.main()
