# ZeroFake: Advanced KYC Fraud Detection System v2.0.0

A production-grade KYC fraud detection platform combining advanced ML models, enterprise security, and MongoDB persistence with a modern React frontend.

## 🎯 Key Features

- **Advanced Face Recognition**: DeepFace + FaceNet-PyTorch dual-model verification
- **Liveness Detection**: MediaPipe + OpenCV multi-method ensemble (texture, blink, motion)
- **Document Forgery Detection**: CNN-based ensemble (ResNet50 + VGG16 + ELA)
- **OCR Engine**: Tesseract with Nepali support for document text extraction
- **Enterprise Security**: JWT authentication, bcrypt password hashing, rate limiting
- **MongoDB Persistence**: Async database operations with motor driver
- **Role-Based Access**: Analyst, Admin, Reviewer roles with fine-grained permissions
- **Feedback Loop**: Continuous model retraining from analyst verdicts

## Architecture

**Backend Stack:**
- Framework: FastAPI + Uvicorn
- Database: MongoDB (async via Motor)
- ML/DL: TensorFlow, PyTorch, DeepFace, MediaPipe, OpenCV
- Security: PyJWT, Passlib/bcrypt, python-jose
- Language: Python 3.9+

**Frontend Stack:**
- Framework: React 18+
- Builder: Vite
- Styling: Tailwind CSS

**Processing Layers:**
1. Authentication & Session Management
2. Rate Limiting & Input Validation
3. KYC Submission Ingestion
4. Pre-screening Engine
5. Document Analysis (Forgery Detection + OCR)
6. Biometric Verification (Face + Liveness)
7. Identity Deduplication
8. Risk Scoring & Decision Routing
9. Feedback Collection & Model Retraining

## Project Structure

```
KYC_Fraud_Detection/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app with auth & endpoints
│   ├── models.py               # Pydantic data models
│   ├── pipeline.py             # KYC processing pipeline
│   ├── engines.py              # Risk scoring engines
│   ├── risk.py                 # Risk assessment logic
│   ├── feedback.py             # Feedback collection & retraining
│   ├── db/                     # Database layer
│   │   ├── __init__.py
│   │   ├── config.py           # MongoDB connection & settings
│   │   └── models.py           # 7 document schemas (KYC, Feedback, User, Session, etc)
│   ├── security/               # Security layer
│   │   ├── __init__.py
│   │   ├── auth.py             # JWT, password hashing, session management
│   │   └── rate_limiter.py     # Rate limiting & input validation
│   └── ml_models/              # Advanced ML engines
│       ├── __init__.py
│       ├── face_recognition.py # DeepFace + FaceNet
│       ├── document_forgery.py # ResNet50 + VGG16 + ELA
│       ├── liveness_detection.py # MediaPipe + OpenCV
│       └── ocr.py              # Tesseract OCR
├── src/
│   ├── App.jsx                 # React main app
│   ├── main.jsx
│   ├── index.css
│   └── data/
│       └── samplePayload.js
├── tests/
│   └── test_pipeline.py
├── requirements.txt            # 35+ Python packages
├── .env.example                # Configuration template
├── package.json                # Frontend dependencies
├── vite.config.js
├── tailwind.config.js
└── README.md
```

## Installation & Setup

### Prerequisites
- Python 3.9+
- Node.js 16+
- MongoDB 4.6+ running locally or remote
- Tesseract OCR engine installed

### Backend Setup

1. **Clone & navigate:**
```bash
cd KYC_Fraud_Detection
```

2. **Create virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\Activate.ps1
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your MongoDB URL and JWT secret
```

5. **Start MongoDB:**
```bash
mongod  # or use Docker: docker run -d -p 27017:27017 mongo:latest
```

6. **Run backend:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
npm install
npm run dev
```

Open browser: `http://localhost:5173`

## API Endpoints

### Authentication
- `POST /auth/register` - Register new analyst/admin user
- `POST /auth/login` - Authenticate and get JWT token
- `POST /auth/logout` - Revoke session

### KYC Processing (Protected)
- `POST /kyc/submit` - Submit KYC for evaluation (requires auth)
- `POST /feedback/verdict` - Submit analyst verdict (analyst+ role)
- `GET /feedback/stats` - Get feedback statistics (analyst+ role)

### Admin (Protected)
- `GET /admin/submissions` - List all KYC submissions (admin role)
- `GET /admin/users` - List system users (admin role)
- `POST /admin/retrain` - Trigger model retraining (admin role)

### Health
- `GET /health` - Server health check

## Decision Outcomes

- `auto_approve` - Submission passes all checks
- `step_up_verification` - Requires additional verification
- `manual_review` - Needs analyst review
- `auto_reject` - Submission fails risk criteria

## Authentication & Authorization

**User Roles:**
- `analyst` - Can submit KYC and provide verdicts
- `reviewer` - Can review submissions and approve/reject
- `admin` - Full access to system configuration and user management

**JWT Token:**
- Issued on login with 24-hour expiration
- Required in `Authorization: Bearer <token>` header
- Validated on all protected endpoints
- Sessions stored in MongoDB for revocation

**Rate Limiting:**
- IP-based: 50 requests/minute (15-minute ban)
- Device-based: 30 requests/minute (15-minute ban)
- User-based: 100 requests/minute (15-minute ban)

## ML Models Details

### Face Recognition
- **Models**: DeepFace (Facenet512) + FaceNet-PyTorch (InceptionResnetV1)
- **Task**: Verify selfie matches document photo
- **Output**: Similarity score (0-1), match verdict
- **Threshold**: 0.90 (configurable)

### Liveness Detection
- **Input**: Image/video frame
- **Methods**: 
  - Texture analysis (Laplacian variance)
  - Blink detection (eye aspect ratio)
  - Motion tracking (landmark movement)
  - Face detection confirmation
- **Weights**: 30% texture + 30% blink + 20% motion + 20% detection
- **Output**: Liveness score, risk level (low/medium/high/critical)

### Document Forgery Detection
- **Methods**:
  - ELA (Error Level Analysis): JPEG recompression artifacts
  - ResNet50: CNN feature extraction
  - VGG16: Complementary architecture
- **Ensemble**: Combined scoring with threshold 0.80
- **Output**: Forgery score, risk level, recommendation

### OCR Engine
- **Language**: English + Nepali
- **Preprocessing**: CLAHE, denoising, thresholding, morphological ops
- **Extraction**: Text + structured fields (dates, IDs, names, emails)
- **Quality Check**: Confidence threshold, word count, symbol ratio
- **Output**: Extracted text, confidence score, field data

## MongoDB Collections

1. **kyc_submissions** - All KYC requests with decisions
2. **feedback_verdicts** - Analyst verdicts for model training
3. **users** - System users with hashed passwords
4. **session_tokens** - Active JWT sessions with expiration
5. **rate_limit_logs** - IP/device/user request tracking
6. **model_training_logs** - Model retraining history
7. **deduplication_store** - Face embedding cache for duplicate detection

## Environment Variables

```
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=zerofake

JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

RATE_LIMIT_IP_REQUESTS_PER_MINUTE=50
RATE_LIMIT_DEVICE_REQUESTS_PER_MINUTE=30
RATE_LIMIT_USER_REQUESTS_PER_MINUTE=100

FACE_SIMILARITY_THRESHOLD=0.90
LIVENESS_CONFIDENCE_THRESHOLD=0.85
FORGERY_DETECTION_THRESHOLD=0.80
```

## Example Usage

### 1. Register User
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "analyst1",
    "email": "analyst@example.com",
    "password": "securepassword123"
  }'
```

### 2. Login
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "analyst1",
    "password": "securepassword123"
  }'
```

### 3. Submit KYC (with JWT token)
```bash
curl -X POST "http://localhost:8000/kyc/submit" \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d @sample_kyc_payload.json
```

### 4. Submit Feedback Verdict
```bash
curl -X POST "http://localhost:8000/feedback/verdict" \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "submission_id": "sub-2001",
    "verdict_decision": "auto_approve",
    "analyst_confidence": 0.95,
    "notes": "All documents verified"
  }'
```

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/test_pipeline.py -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=html
```

## Troubleshooting

**Tesseract not found:**
```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Windows
Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

**MongoDB connection error:**
- Verify MongoDB is running: `mongosh` or `mongo`
- Check MONGODB_URL in .env file
- Ensure port 27017 is accessible

**ML models slow to load:**
- First initialization downloads model weights (~2-3 GB total)
- Models are cached after first load (singleton pattern)
- Subsequent loads are instant

## Performance Notes

- Face recognition: ~200-500ms per image pair
- Liveness detection: ~300-800ms per video frame
- Document forgery: ~400-600ms per image
- OCR: ~500-1500ms depending on image quality
- End-to-end KYC: ~2-5 seconds (parallel processing)

## Security Considerations

✅ **Implemented:**
- HTTPS middleware ready (uncomment in main.py)
- JWT token validation on all protected endpoints
- Password hashing with bcrypt (10 rounds)
- Rate limiting at IP/device/user levels
- Input validation and sanitization
- MongoDB session tracking and revocation
- Role-based access control

⚠️ **For Production:**
- Set strong JWT_SECRET_KEY (use `secrets.token_urlsafe()`)
- Enable HTTPS/TLS
- Use managed MongoDB (Atlas, DocumentDB)
- Configure firewall rules
- Implement audit logging
- Set up monitoring and alerting
- Rotate secrets regularly

## Contributing

1. Create feature branch
2. Make changes with tests
3. Run: `pytest tests/ -v`
4. Commit with clear messages
5. Submit PR

## License

Proprietary - All rights reserved

## Support

For issues, questions, or feature requests, contact the development team.
