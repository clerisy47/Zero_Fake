# ZeroFake Quick Start Guide

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Verify installation
python3 -c "from app.main import app; print('✅ Ready to run')"
```

## Running the Server

```bash
# Development
uvicorn app.main:app --reload

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Server will be available at: `http://localhost:8000`

## API Usage Examples

### 1. Submit KYC for Evaluation

```bash
curl -X POST "http://localhost:8000/kyc/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "submission_id": "sub_001",
    "channel": "web",
    "claimed_country": "Nepal",
    "gateway": {
      "tls_valid": true,
      "ip_requests_last_minute": 2,
      "device_requests_last_minute": 1,
      "session_token_valid": true
    },
    "device": {
      "canvas_fingerprint_hash": "abc123def456",
      "installed_font_count": 42,
      "user_agent": "Mozilla/5.0...",
      "accelerometer_variance": 0.15,
      "webgl_renderer_hash": "Intel HD Graphics",
      "device_id": "dev_12345",
      "known_recent_submission_count": 0,
      "os_family": "macOS"
    },
    "network": {
      "ip": "192.168.1.100",
      "is_vpn": false,
      "is_tor": false,
      "is_datacenter_proxy": false,
      "country": "Nepal",
      "asn_type": "ISP"
    },
    "behavior": {
      "form_completion_seconds": 45.5,
      "copy_paste_events": 1,
      "typing_interval_stddev_ms": 95.0,
      "mouse_path_entropy": 2.5
    },
    "document": {
      "document_type": "Passport",
      "issuing_country": "Nepal",
      "document_number": "PA-123456789",
      "full_name": "Raj Kumar",
      "dob": "1990-05-15",
      "claimed_age": 34,
      "expiry": "2028-05-15",
      "ela_score": 0.1,
      "font_match_score": 0.95,
      "mrz_checksum_valid": true,
      "template_match_score": 0.92,
      "image_quality_score": 0.88,
      "ocr_field_validation": 0.9,
      "hologram_confidence": 0.85,
      "nepal_district": "Kathmandu"
    },
    "biometric": {
      "liveness_score": 0.92,
      "face_similarity_score": 0.88,
      "face_embedding": [0.1, 0.2, 0.3],
      "deepfake_score": 0.05,
      "camera_injection_detected": false,
      "estimated_age": 34
    }
  }'
```

**Response:**
```json
{
  "submission_id": "sub_001",
  "decision": "auto_approve",
  "risk_score": 18.5,
  "hard_fail": null,
  "reason_codes": ["GATEWAY_TLS_OK", "PRESCREEN_NETWORK_RISK_OK"],
  "risk_breakdown": {
    "category_scores": {
      "gateway": 2.1,
      "pre_screen": 5.3,
      "document": 12.4,
      "biometric": 3.2,
      "dedup": 0.0
    },
    "blended_score": 18.5
  },
  "layer_results": [...],
  "processing_time_ms": 3245
}
```

### 2. Submit Analyst Verdict (Feedback Loop)

After an analyst reviews a decision, submit their verdict to improve the model:

```bash
curl -X POST "http://localhost:8000/feedback/verdict" \
  -H "Content-Type: application/json" \
  -d '{
    "submission_id": "sub_001",
    "verdict_decision": "auto_approve",
    "analyst_confidence": 0.95,
    "notes": "Document verified. Applicant appears legitimate."
  }'
```

**Response:**
```json
{
  "status": "verdict_recorded",
  "submission_id": "sub_001",
  "model_retraining_triggered": false,
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

### 3. Check Feedback Statistics

```bash
curl -X GET "http://localhost:8000/feedback/stats"
```

**Response:**
```json
{
  "weekly_verdicts_count": 45,
  "reject_verdicts": 12,
  "approve_verdicts": 33,
  "retraining_needed": false,
  "last_retrain_time": "2024-01-08T14:22:10.123456"
}
```

### 4. Trigger Model Retraining (Admin)

```bash
curl -X POST "http://localhost:8000/admin/retrain"
```

**Response:**
```json
{
  "status": "retrained_successfully",
  "samples_used": 325,
  "retraining_timestamp": "2024-01-15T15:45:30.123456",
  "message": "Model retraining completed with analyst verdicts from the past 12 weeks."
}
```

### 5. Health Check

```bash
curl -X GET "http://localhost:8000/health"
```

**Response:**
```json
{
  "status": "ok"
}
```

## Decision Outcomes

| Risk Score | Decision | Interpretation |
|-----------|----------|-----------------|
| < 25 | `auto_approve` | ✅ Application approved automatically |
| 25-50 | `step_up_verification` | ⚠️ Additional verification required |
| 50-75 | `manual_review` | 👁️ Requires analyst review |
| ≥ 75 | `auto_reject` | ❌ Application rejected automatically |

## Hard-Fail Conditions

Applications are automatically rejected if:
- TLS validation fails at gateway
- Session token is invalid/expired
- Document MRZ checksum invalid
- Invalid Nepal district (if Nepal-issued)
- Camera injection detected
- Liveness score < 0.2
- Exact document number reuse detected

## Supported Nepal Districts (77)

```
Kathmandu, Bhaktapur, Lalitpur, Kavre, Nuwakot, Rasuwa, Sindhuli,
Makawanpur, Rautahat, Bara, Parsa, Dhanusha, Mahottari, Saptari,
Sunsari, Ilam, Jhapa, Morang, Sankhuwasabha, Terhathum, Panchthar,
Taplejung, Okhaldhunga, Khotang, Udayapur, Janakpur, Siraha, Sarlahi,
Chitwan, Nawalpur, Parasi, Gulmi, Arghakhanchi, Kapilvastu, Rupandehi,
Dang, Salyan, Rolpa, Pyuthan, Gorkha, Lamjung, Tanahu, Syangja,
Kaski, Manang, Mustang, Myagdi, Parbat, Baglung, Dolakha, Ramechhap,
Solukhumbu, Bhojpur, Dhankuta, Tehrathum, Taplejung, Jumla, Mugu,
Humla, Bajhang, Bajura, Dadeldhura, Baitadi, Doti, Achham, Kailali,
Kanchanpur
```

## Feedback Loop Workflow

1. **Application Submitted** → `/kyc/submit` → Decision + Risk Score
2. **Analyst Reviews** → Dashboard review
3. **Verdict Submitted** → `/feedback/verdict` → Stored in JSONL
4. **Feedback Accumulates** → Tracked weekly
5. **Retraining Triggered** → Weekly OR after 100 verdicts
6. **Model Improves** → Better accuracy with analyst feedback

## Performance Characteristics

- **Total Pipeline Time:** ~3-5 seconds (target: <8 seconds) ✅
- **Gateway Layer:** <1ms
- **Pre-screening:** <20ms (target: <200ms) ✅
- **Document Analysis:** <1000ms
- **Biometric Check:** <1500-2000ms
- **Deduplication:** <100ms
- **Scoring & Decision:** <100ms

## Troubleshooting

### Import Errors
```bash
# Verify all modules import
python3 -c "from app.models import *; from app.engines import *; from app.feedback import *; print('✅ OK')"
```

### Feedback File Issues
```bash
# Feedback data stored in:
ls -la feedback_data/verdicts.jsonl

# To reset feedback:
rm -rf feedback_data/
```

### Testing with Sample Payload
```bash
# Use the samplePayload from frontend
python3 -c "from src.data.samplePayload import sample; import json; print(json.dumps(sample, indent=2))"
```

## Documentation

- **Full Implementation Details:** See `ZEROFAKE_IMPLEMENTATION.md`
- **README:** See `README.md`
- **KYC Report:** See `KYC_Fraud_Detection_Report.md`

## Next Steps

1. Start the server: `uvicorn app.main:app --reload`
2. Submit test KYC applications
3. Monitor with `/feedback/stats`
4. Collect analyst verdicts
5. Schedule weekly retraining
6. Deploy to production
