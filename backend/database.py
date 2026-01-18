"""
MongoDB Database Configuration and Models
"""

import os
from datetime import datetime
from typing import Optional, List, Any, Annotated
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, ConfigDict, field_validator
from bson import ObjectId


# Pydantic Models (simplified for Pydantic v2)
class GapModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

    id: Optional[Any] = Field(default=None, alias="_id")
    session_id: str
    timestamp: datetime
    duration: float  # seconds
    session_time: float  # seconds since session start
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TranscriptModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

    id: Optional[Any] = Field(default=None, alias="_id")
    room_name: str
    text: str
    start_time: float  # seconds since session start
    end_time: float  # seconds since session start
    is_final: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SessionModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

    id: Optional[Any] = Field(default=None, alias="_id")
    room_name: str
    student_identity: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    total_duration: Optional[float] = None  # seconds
    total_gaps: int = 0


# Database connection
class Database:
    client: Optional[AsyncIOMotorClient] = None
    db = None

    @classmethod
    async def connect_db(cls):
        """Connect to MongoDB Atlas"""
        mongodb_uri = os.getenv("MONGODB_URI")
        db_name = os.getenv("MONGODB_DB_NAME", "hindsight")

        if not mongodb_uri or "<username>" in mongodb_uri:
            print("WARNING: MongoDB URI not configured - running without database")
            return

        try:
            cls.client = AsyncIOMotorClient(mongodb_uri, serverSelectionTimeoutMS=5000)
            cls.db = cls.client[db_name]

            # Test connection with shorter timeout
            await cls.client.admin.command('ping')
            print(f"SUCCESS: Connected to MongoDB Atlas - Database: {db_name}")

            # Create indexes
            await cls.db.gaps.create_index("session_id")
            await cls.db.gaps.create_index("timestamp")
            await cls.db.sessions.create_index("room_name")
            await cls.db.sessions.create_index("started_at")
            await cls.db.transcripts.create_index("room_name")
            await cls.db.transcripts.create_index([("room_name", 1), ("start_time", 1)])

        except Exception as e:
            print(f"ERROR: Failed to connect to MongoDB: {e}")
            print("WARNING: Running without database - data will not persist")
            cls.client = None
            cls.db = None

    @classmethod
    async def close_db(cls):
        """Close MongoDB connection"""
        if cls.client:
            cls.client.close()
            print("INFO: MongoDB connection closed")

    @classmethod
    def get_db(cls):
        """Get database instance"""
        return cls.db


# Database instance
db = Database()
