# KYC Fraud Detection Pipeline

A production-style KYC fraud detection project with a clean React + Tailwind frontend and an unchanged FastAPI backend.

## Project Overview

- Backend: FastAPI app under `app/`.
- Frontend: Root-level Vite + React + Tailwind app under `src/`.
- No backend changes were made as requested.

## Implemented Layers

1. Submission ingestion gateway
2. Pre-screening engine
3. Document analysis engine
4. Biometric verification engine
5. Identity deduplication engine
6. Risk scoring engine
7. Decision routing

## Decision Outcomes

- `auto_approve`
- `step_up_verification`
- `manual_review`
- `auto_reject`

## Frontend Details

The frontend includes:

- Home dashboard with product summary and deployment hints.
- Submit page with a structured KYC form, sample payload loader, request preview, and result display.
- Docs page showing API contract and payload examples.
- About page explaining decision outcomes and workflow.

UI files:

- `src/App.jsx`
- `src/main.jsx`
- `src/index.css`
- `src/data/samplePayload.js`

## Run

### Backend
From the project root:

```powershell
cd "D:\Esewa Hackothon\KYC_Fraud_Detection"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend
From the project root:

```bash
npm install
npm run dev
```

Open the browser at:

- `http://localhost:5173`

Then use the **Submit** page to send requests to the backend.

## API

- `GET /health` — backend health check
- `POST /kyc/submit` — submit a KYC payload and receive a decision

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
python -m unittest discover -s tests -p "test_*.py"
```

## Notes

- The frontend is a polished React + Tailwind app.
- The backend remains unchanged.
- `npm install` and `npm run dev` should be run from the root directory.
