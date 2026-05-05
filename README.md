# KYC Fraud Detection Pipeline

This project implements a layered fraud detection pipeline for KYC submissions.

## Implemented Layers

1. Submission ingestion gateway
2. Pre-screening engine
3. Document analysis engine
4. Biometric verification engine
5. Identity deduplication engine
6. Risk scoring engine
7. Decision routing

## Decision Outcomes

- auto_approve
- step_up_verification
- manual_review
- auto_reject

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## API

- `GET /health`
- `POST /kyc/submit`

Example request payload:

```json
{
  "submission_id": "sub-2001",
  "channel": "web",
  "claimed_country": "Nepal",
  "gateway": {
    "tls_valid": true,
    "ip_requests_last_minute": 6,
    "device_requests_last_minute": 2,
    "session_token_valid": true
  },
  "device": {
    "device_id": "dev-q1",
    "known_recent_submission_count": 1,
    "user_agent": "Mozilla/5.0",
    "os_family": "iOS"
  },
  "network": {
    "ip": "103.40.1.10",
    "is_vpn": false,
    "is_tor": false,
    "is_datacenter_proxy": false,
    "country": "Nepal",
    "asn_type": "retail"
  },
  "behavior": {
    "form_completion_seconds": 72,
    "copy_paste_events": 0,
    "typing_interval_stddev_ms": 230,
    "mouse_path_entropy": 0.61
  },
  "document": {
    "document_type": "passport",
    "issuing_country": "Nepal",
    "document_number": "NEP-987654-10",
    "full_name": "Sita Poudel",
    "dob": "1990-06-11",
    "claimed_age": 35,
    "expiry": "2031-06-11",
    "ela_score": 0.1,
    "font_match_score": 0.93,
    "mrz_checksum_valid": true,
    "template_match_score": 0.95,
    "image_quality_score": 0.9
  },
  "biometric": {
    "liveness_score": 0.91,
    "face_similarity_score": 0.88,
    "deepfake_score": 0.08,
    "camera_injection_detected": false,
    "estimated_age": 34
  }
}
```

## Tests

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

## Notes

- Hard-fail rules force auto-reject.
- All layers emit normalized explainable signals.
- Risk is fused from tabular and biometric components.
