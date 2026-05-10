from __future__ import annotations

import os
from typing import Optional

from motor.motor_asyncio import AsyncClient, AsyncDatabase
from pydantic import Field
from pydantic_settings import BaseSettings

# Configuration
class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    mongodb_url: str = Field(default="mongodb://localhost:27017", alias="MONGODB_URL")
    mongodb_db: str = Field(default="zerofake", alias="MONGODB_DB")
    jwt_secret_key: str = Field(default="your-secret-key-change-in-production", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

# Database connection
class Database:
    """MongoDB database connection manager."""
    
    client: Optional[AsyncClient] = None
    db: Optional[AsyncDatabase] = None
    
    @classmethod
    async def connect_db(cls) -> None:
        """Connect to MongoDB."""
        cls.client = AsyncClient(settings.mongodb_url)
        cls.db = cls.client[settings.mongodb_db]
        # Verify connection
        try:
            await cls.db.command("ping")
            print("✅ MongoDB connected successfully")
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            raise
    
    @classmethod
    async def close_db(cls) -> None:
        """Close MongoDB connection."""
        if cls.client:
            cls.client.close()
            print("✅ MongoDB connection closed")
    
    @classmethod
    def get_db(cls) -> AsyncDatabase:
        """Get database instance."""
        if cls.db is None:
            raise RuntimeError("Database not connected. Call connect_db() first.")
        return cls.db


async def get_database() -> AsyncDatabase:
    """Dependency injection for database."""
    return Database.get_db()
