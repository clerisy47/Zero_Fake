from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from passlib.context import CryptContext
from motor.motor_asyncio import AsyncDatabase

from app.db.config import get_database
from app.db.models import SessionTokenDocument, UserDocument


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
JWT_ALGORITHM = "HS256"
JWT_SECRET_KEY = "your-secret-key-change-in-production"  # Set from env in production
JWT_EXPIRATION_HOURS = 24

# Security scheme
security = HTTPBearer()


class AuthenticationManager:
    """Manages user authentication and JWT tokens."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        if expires_delta is None:
            expires_delta = timedelta(hours=JWT_EXPIRATION_HOURS)
        
        expire = datetime.utcnow() + expires_delta
        to_encode = {
            "user_id": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
        }
        
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> dict:
        """Verify a JWT token and return payload."""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )


class SessionManager:
    """Manages user sessions and tokens in MongoDB."""
    
    @staticmethod
    async def create_session(
        db: AsyncDatabase,
        user_id: str,
        ip_address: str,
        device_fingerprint: str,
    ) -> str:
        """Create a new session and return token."""
        token = secrets.token_urlsafe(32)
        
        session_doc = SessionTokenDocument(
            token=token,
            user_id=user_id,
            ip_address=ip_address,
            device_fingerprint=device_fingerprint,
            expires_at=datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
            is_active=True,
        )
        
        await db.session_tokens.insert_one(session_doc.model_dump(by_alias=True))
        return token
    
    @staticmethod
    async def verify_session(db: AsyncDatabase, token: str) -> Optional[dict]:
        """Verify if session token is valid and active."""
        session = await db.session_tokens.find_one({
            "token": token,
            "is_active": True,
            "expires_at": {"$gt": datetime.utcnow()},
        })
        return session
    
    @staticmethod
    async def revoke_session(db: AsyncDatabase, token: str, reason: str = "user_logout") -> None:
        """Revoke a session token."""
        await db.session_tokens.update_one(
            {"token": token},
            {
                "$set": {
                    "is_active": False,
                    "revoked_at": datetime.utcnow(),
                    "revoke_reason": reason,
                }
            },
        )
    
    @staticmethod
    async def revoke_user_sessions(db: AsyncDatabase, user_id: str) -> None:
        """Revoke all sessions for a user."""
        await db.session_tokens.update_many(
            {"user_id": user_id, "is_active": True},
            {
                "$set": {
                    "is_active": False,
                    "revoked_at": datetime.utcnow(),
                    "revoke_reason": "user_logout_all",
                }
            },
        )


async def get_current_user(
    credentials: HTTPAuthCredentials = Depends(security),
    db: AsyncDatabase = Depends(get_database),
) -> dict:
    """Dependency to get current authenticated user."""
    token = credentials.credentials
    
    # Verify JWT token
    payload = AuthenticationManager.verify_token(token)
    user_id: str = payload.get("user_id")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify session exists in database
    session = await SessionManager.verify_session(db, token)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user details
    user = await db.users.find_one({"_id": user_id})
    if user is None or not user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_admin_user(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Dependency to ensure user is admin."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def get_analyst_user(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Dependency to ensure user is analyst or admin."""
    if current_user.get("role") not in ["analyst", "admin", "reviewer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Analyst access required",
        )
    return current_user
