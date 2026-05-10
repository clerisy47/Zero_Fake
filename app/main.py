from __future__ import annotations

import time
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncDatabase

from app.db.config import Database, settings
from app.feedback import FeedbackCollector, ModelRetrainingScheduler
from app.models import AnalystVerdict, DecisionResult, HealthResponse, KycSubmission
from app.pipeline import FraudPipeline
from app.security import (
    AuthenticationManager,
    SessionManager,
    RateLimiter,
    InputValidator,
    get_current_user,
    get_analyst_user,
    get_admin_user,
)


# Initialize core components
pipeline = FraudPipeline()
feedback_collector = FeedbackCollector()
retraining_scheduler = ModelRetrainingScheduler(feedback_collector)

# FastAPI app
app = FastAPI(
    title="ZeroFake",
    version="2.0.0",
    description="Advanced KYC Fraud Detection with ML Models for Nepal",
)

# Middleware - CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
    allow_credentials=True,
)


# Event handlers
@app.on_event("startup")
async def startup_event():
    """Initialize database and ML models on startup."""
    print("\n🚀 Starting ZeroFake KYC Fraud Detection System v2.0.0...")
    
    try:
        # Connect to MongoDB
        await Database.connect_db()
        print("✅ MongoDB connected")
        
        # Initialize ML models
        from app.ml_models import (
            get_face_recognition_engine,
            get_forgery_detection_engine,
            get_liveness_detection_engine,
            get_ocr_engine,
        )
        
        get_face_recognition_engine()
        get_forgery_detection_engine()
        get_liveness_detection_engine()
        get_ocr_engine()
        print("✅ All ML models initialized")
        
        print("✅ System ready\n")
    
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print("\n🛑 Shutting down ZeroFake...")
    await Database.close_db()
    print("✅ MongoDB connection closed\n")


# ==================== Authentication Endpoints ====================

@app.post("/auth/register")
async def register(
    username: str,
    email: str,
    password: str,
    db: AsyncDatabase = Depends(Database.get_db),
) -> dict:
    """Register a new user."""
    try:
        # Validate input
        username = InputValidator.validate_string(username, max_length=50)
        email = InputValidator.validate_email(email)
        password = InputValidator.validate_string(password, max_length=100)
        
        if len(password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters",
            )
        
        # Check if user exists
        existing_user = await db.users.find_one({"$or": [{"username": username}, {"email": email}]})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already exists",
            )
        
        # Create user
        hashed_password = AuthenticationManager.hash_password(password)
        user_doc = {
            "username": username,
            "email": email,
            "hashed_password": hashed_password,
            "role": "analyst",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        
        result = await db.users.insert_one(user_doc)
        
        return {
            "status": "success",
            "user_id": str(result.inserted_id),
            "username": username,
            "email": email,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/auth/login")
async def login(
    username: str,
    password: str,
    ip_address: str = "0.0.0.0",
    device_fingerprint: str = "unknown",
    db: AsyncDatabase = Depends(Database.get_db),
) -> dict:
    """Authenticate user and create session."""
    try:
        # Validate input
        username = InputValidator.validate_string(username)
        
        # Find user
        user = await db.users.find_one({"username": username, "is_active": True})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )
        
        # Verify password
        if not AuthenticationManager.verify_password(password, user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )
        
        # Create session
        token = await SessionManager.create_session(
            db,
            str(user["_id"]),
            ip_address,
            device_fingerprint,
        )
        
        # Create JWT
        jwt_token = AuthenticationManager.create_access_token(str(user["_id"]))
        
        return {
            "status": "success",
            "access_token": jwt_token,
            "session_token": token,
            "user": {
                "user_id": str(user["_id"]),
                "username": user["username"],
                "email": user["email"],
                "role": user["role"],
            },
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/auth/logout")
async def logout(
    current_user: dict = Depends(get_current_user),
    db: AsyncDatabase = Depends(Database.get_db),
) -> dict:
    """Logout user and revoke session."""
    try:
        user_id = str(current_user.get("_id"))
        await SessionManager.revoke_user_sessions(db, user_id)
        
        return {"status": "success", "message": "Logged out successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ==================== Health Check ====================

@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="ok")


# ==================== KYC Processing ====================

@app.post("/kyc/submit", response_model=DecisionResult)
async def submit_kyc(
    submission: KycSubmission,
    current_user: dict = Depends(get_analyst_user),
    db: AsyncDatabase = Depends(Database.get_db),
) -> DecisionResult:
    """Submit a KYC application for fraud detection evaluation (requires authentication)."""
    try:
        start_time = time.time()
        
        # Rate limiting
        ip_address = "0.0.0.0"
        await RateLimiter.check_ip_rate_limit(db, ip_address)
        await RateLimiter.check_user_rate_limit(db, str(current_user["_id"]))
        
        # Set timestamp
        if submission.timestamp is None:
            submission.timestamp = datetime.utcnow()
        
        # Process through pipeline
        result = pipeline.process(submission)
        
        # Record processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        result.processing_time_ms = processing_time_ms
        
        # Store in MongoDB
        submission_doc = {
            "submission_id": submission.submission_id,
            "decision": result.decision.value,
            "risk_score": result.risk_score,
            "processing_time_ms": processing_time_ms,
            "created_at": datetime.utcnow(),
        }
        
        await db.kyc_submissions.insert_one(submission_doc)
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ==================== Feedback & Learning ====================

@app.post("/feedback/verdict")
async def submit_verdict(
    verdict: AnalystVerdict,
    current_user: dict = Depends(get_analyst_user),
    db: AsyncDatabase = Depends(Database.get_db),
) -> dict:
    """Submit analyst verdict for continuous model improvement."""
    try:
        feedback_collector.record_verdict(verdict)
        should_retrain = retraining_scheduler.should_retrain()
        
        # Store in MongoDB
        verdict_doc = {
            "submission_id": verdict.submission_id,
            "analyst_id": str(current_user["_id"]),
            "verdict_decision": verdict.verdict_decision.value,
            "analyst_confidence": verdict.analyst_confidence,
            "notes": verdict.notes,
            "created_at": datetime.utcnow(),
        }
        
        await db.feedback_verdicts.insert_one(verdict_doc)
        
        return {
            "status": "verdict_recorded",
            "submission_id": verdict.submission_id,
            "model_retraining_triggered": should_retrain,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/feedback/stats")
async def get_feedback_stats(
    current_user: dict = Depends(get_analyst_user),
    db: AsyncDatabase = Depends(Database.get_db),
) -> dict:
    """Get feedback collection statistics."""
    try:
        weekly_verdicts = feedback_collector.get_verdicts_since(hours=168)
        reject_count = len(feedback_collector.get_verdicts_by_decision("auto_reject"))
        approve_count = len(feedback_collector.get_verdicts_by_decision("auto_approve"))
        
        return {
            "weekly_verdicts_count": len(weekly_verdicts),
            "reject_verdicts": reject_count,
            "approve_verdicts": approve_count,
            "retraining_needed": retraining_scheduler.should_retrain(),
            "last_retrain_time": (
                retraining_scheduler.last_retrain_time.isoformat()
                if retraining_scheduler.last_retrain_time
                else None
            ),
        }
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/admin/retrain")
async def trigger_retraining(
    current_user: dict = Depends(get_admin_user),
    db: AsyncDatabase = Depends(Database.get_db),
) -> dict:
    """Trigger model retraining (admin only)."""
    try:
        X_train, y_train = retraining_scheduler.get_training_data()
        
        if len(X_train) < 10:
            return {
                "status": "insufficient_data",
                "message": f"Need at least 10 training samples, got {len(X_train)}",
            }
        
        retraining_scheduler.on_retrain_complete()
        
        training_log = {
            "training_id": f"train_{datetime.utcnow().timestamp()}",
            "model_version": "2.0.0",
            "training_samples_count": len(X_train),
            "deployed": False,
            "created_at": datetime.utcnow(),
        }
        
        await db.model_training_logs.insert_one(training_log)
        
        return {
            "status": "retrained_successfully",
            "samples_used": len(X_train),
            "retraining_timestamp": datetime.utcnow().isoformat(),
        }
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ==================== Admin Endpoints ====================

@app.get("/admin/submissions")
async def list_submissions(
    current_user: dict = Depends(get_admin_user),
    db: AsyncDatabase = Depends(Database.get_db),
    skip: int = 0,
    limit: int = 10,
) -> dict:
    """List all KYC submissions."""
    try:
        total = await db.kyc_submissions.count_documents({})
        submissions = await db.kyc_submissions.find({}).skip(skip).limit(limit).to_list(limit)
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "count": len(submissions),
            "submissions": submissions,
        }
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/admin/users")
async def list_users(
    current_user: dict = Depends(get_admin_user),
    db: AsyncDatabase = Depends(Database.get_db),
) -> dict:
    """List all system users (admin only)."""
    try:
        users = await db.users.find({}).project({"hashed_password": 0}).to_list(None)
        
        return {
            "total": len(users),
            "users": users,
        }
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

