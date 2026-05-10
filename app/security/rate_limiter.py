from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncDatabase

from app.db.models import RateLimitDocument


class RateLimiter:
    """Enhanced rate limiting with IP and device tracking."""
    
    # Rate limits per minute
    IP_REQUESTS_LIMIT = 50
    DEVICE_REQUESTS_LIMIT = 30
    USER_REQUESTS_LIMIT = 100
    
    # Time window (1 minute)
    WINDOW_SECONDS = 60
    
    @staticmethod
    def _get_window_start() -> datetime:
        """Get the start of the current time window."""
        now = datetime.utcnow()
        # Round down to nearest minute
        return now.replace(second=0, microsecond=0)
    
    @classmethod
    async def check_ip_rate_limit(
        cls,
        db: AsyncDatabase,
        ip_address: str,
    ) -> bool:
        """Check if IP has exceeded rate limit."""
        window_start = cls._get_window_start()
        
        # Get or create rate limit document
        limit_doc = await db.rate_limits.find_one({
            "identifier": ip_address,
            "identifier_type": "ip",
            "window_start": window_start,
        })
        
        if limit_doc is None:
            # First request in this window
            await db.rate_limits.insert_one({
                "identifier": ip_address,
                "identifier_type": "ip",
                "request_count": 1,
                "window_start": window_start,
                "last_request_at": datetime.utcnow(),
                "is_blocked": False,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            })
            return True
        
        # Check if blocked
        if limit_doc.get("is_blocked"):
            blocked_until = limit_doc.get("blocked_until")
            if blocked_until and blocked_until > datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Try again after {blocked_until}",
                )
        
        # Increment counter
        new_count = limit_doc.get("request_count", 0) + 1
        
        # Check if exceeded
        if new_count > cls.IP_REQUESTS_LIMIT:
            # Block for next 15 minutes
            blocked_until = datetime.utcnow() + timedelta(minutes=15)
            await db.rate_limits.update_one(
                {"_id": limit_doc["_id"]},
                {
                    "$set": {
                        "request_count": new_count,
                        "is_blocked": True,
                        "blocked_until": blocked_until,
                        "last_request_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    }
                },
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded (IP: {cls.IP_REQUESTS_LIMIT}/min). Try again after {blocked_until}",
            )
        
        # Update counter
        await db.rate_limits.update_one(
            {"_id": limit_doc["_id"]},
            {
                "$set": {
                    "request_count": new_count,
                    "last_request_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            },
        )
        
        return True
    
    @classmethod
    async def check_device_rate_limit(
        cls,
        db: AsyncDatabase,
        device_fingerprint: str,
    ) -> bool:
        """Check if device has exceeded rate limit."""
        window_start = cls._get_window_start()
        
        limit_doc = await db.rate_limits.find_one({
            "identifier": device_fingerprint,
            "identifier_type": "device",
            "window_start": window_start,
        })
        
        if limit_doc is None:
            await db.rate_limits.insert_one({
                "identifier": device_fingerprint,
                "identifier_type": "device",
                "request_count": 1,
                "window_start": window_start,
                "last_request_at": datetime.utcnow(),
                "is_blocked": False,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            })
            return True
        
        if limit_doc.get("is_blocked"):
            blocked_until = limit_doc.get("blocked_until")
            if blocked_until and blocked_until > datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Device rate limit exceeded. Try again after {blocked_until}",
                )
        
        new_count = limit_doc.get("request_count", 0) + 1
        
        if new_count > cls.DEVICE_REQUESTS_LIMIT:
            blocked_until = datetime.utcnow() + timedelta(minutes=15)
            await db.rate_limits.update_one(
                {"_id": limit_doc["_id"]},
                {
                    "$set": {
                        "request_count": new_count,
                        "is_blocked": True,
                        "blocked_until": blocked_until,
                        "last_request_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    }
                },
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded (Device: {cls.DEVICE_REQUESTS_LIMIT}/min). Try again after {blocked_until}",
            )
        
        await db.rate_limits.update_one(
            {"_id": limit_doc["_id"]},
            {
                "$set": {
                    "request_count": new_count,
                    "last_request_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            },
        )
        
        return True
    
    @classmethod
    async def check_user_rate_limit(
        cls,
        db: AsyncDatabase,
        user_id: str,
    ) -> bool:
        """Check if user has exceeded rate limit."""
        window_start = cls._get_window_start()
        
        limit_doc = await db.rate_limits.find_one({
            "identifier": user_id,
            "identifier_type": "user",
            "window_start": window_start,
        })
        
        if limit_doc is None:
            await db.rate_limits.insert_one({
                "identifier": user_id,
                "identifier_type": "user",
                "request_count": 1,
                "window_start": window_start,
                "last_request_at": datetime.utcnow(),
                "is_blocked": False,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            })
            return True
        
        new_count = limit_doc.get("request_count", 0) + 1
        
        if new_count > cls.USER_REQUESTS_LIMIT:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"User rate limit exceeded ({cls.USER_REQUESTS_LIMIT}/min). Try again later.",
            )
        
        await db.rate_limits.update_one(
            {"_id": limit_doc["_id"]},
            {
                "$set": {
                    "request_count": new_count,
                    "last_request_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            },
        )
        
        return True
    
    @classmethod
    async def cleanup_expired_limits(cls, db: AsyncDatabase) -> int:
        """Clean up expired rate limit records (older than 2 hours)."""
        cutoff_time = datetime.utcnow() - timedelta(hours=2)
        
        result = await db.rate_limits.delete_many({
            "last_request_at": {"$lt": cutoff_time},
        })
        
        return result.deleted_count


class InputValidator:
    """Input validation and attack prevention."""
    
    # Maximum lengths for various fields
    MAX_STRING_LENGTH = 1000
    MAX_TEXT_LENGTH = 10000
    MAX_IP_LENGTH = 45
    MAX_EMAIL_LENGTH = 254
    
    @staticmethod
    def validate_string(value: str, max_length: int = MAX_STRING_LENGTH) -> str:
        """Validate and sanitize string input."""
        if not isinstance(value, str):
            raise ValueError("Value must be a string")
        
        if len(value) > max_length:
            raise ValueError(f"String exceeds maximum length of {max_length}")
        
        # Remove potentially dangerous characters
        dangerous_chars = ["<", ">", "{", "}", "$", "%"]
        for char in dangerous_chars:
            if char in value:
                raise ValueError(f"String contains potentially dangerous character: {char}")
        
        return value.strip()
    
    @staticmethod
    def validate_ip_address(ip: str) -> str:
        """Validate IP address format."""
        import ipaddress
        
        if len(ip) > InputValidator.MAX_IP_LENGTH:
            raise ValueError("IP address too long")
        
        try:
            ipaddress.ip_address(ip)
            return ip
        except ValueError:
            raise ValueError(f"Invalid IP address format: {ip}")
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email format."""
        import re
        
        if len(email) > InputValidator.MAX_EMAIL_LENGTH:
            raise ValueError("Email too long")
        
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, email):
            raise ValueError("Invalid email format")
        
        return email.lower()
    
    @staticmethod
    def validate_device_fingerprint(fingerprint: str) -> str:
        """Validate device fingerprint format."""
        if len(fingerprint) < 32 or len(fingerprint) > 256:
            raise ValueError("Invalid device fingerprint length")
        
        import re
        if not re.match(r"^[a-f0-9]+$", fingerprint.lower()):
            raise ValueError("Device fingerprint must be hexadecimal")
        
        return fingerprint.lower()
