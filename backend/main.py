"""
Hindsight Backend - FastAPI Server
Token Generation for LiveKit + MongoDB Persistence
"""

import os
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from livekit import api
from dotenv import load_dotenv
from database import db, GapModel, SessionModel, TranscriptModel

# Load environment variables from .env.local in project root
env_path = Path(__file__).parent.parent / ".env.local"
load_dotenv(env_path)

app = FastAPI(
    title="Hindsight API",
    description="Token Generation for LiveKit Voice Agent + MongoDB Persistence",
    version="0.2.0"
)


# Lifecycle events
@app.on_event("startup")
async def startup_event():
    """Connect to MongoDB on startup"""
    await db.connect_db()


@app.on_event("shutdown")
async def shutdown_event():
    """Close MongoDB connection on shutdown"""
    await db.close_db()

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TokenResponse(BaseModel):
    token: str
    url: str


class CreateSessionRequest(BaseModel):
    room_name: str
    student_identity: str = "student-user"


class CreateGapRequest(BaseModel):
    session_id: str
    timestamp: datetime
    duration: float
    session_time: float


class SessionResponse(BaseModel):
    id: str
    room_name: str
    student_identity: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    total_duration: Optional[float] = None
    total_gaps: int = 0


class GapResponse(BaseModel):
    id: str
    session_id: str
    timestamp: datetime
    duration: float
    session_time: float
    created_at: datetime


class CreateTranscriptRequest(BaseModel):
    room_name: str
    text: str
    start_time: float
    end_time: float
    is_final: bool = True


class TranscriptResponse(BaseModel):
    id: str
    room_name: str
    text: str
    start_time: float
    end_time: float
    is_final: bool
    created_at: datetime


@app.get("/")
async def root():
    return {"message": "Hindsight API", "status": "running"}


@app.get("/token", response_model=TokenResponse)
async def get_token(room_name: str, identity: str = "student-user"):
    """
    Generate a LiveKit access token for the frontend to join a room.
    
    Args:
        room_name: The name of the room to join
        identity: The identity of the participant (default: student-user)
        
    Returns:
        Access token and LiveKit server URL
    """
    try:
        # Get LiveKit credentials from environment
        livekit_url = os.getenv("LIVEKIT_URL", "")
        api_key = os.getenv("LIVEKIT_API_KEY", "")
        api_secret = os.getenv("LIVEKIT_API_SECRET", "")
        
        if not api_key or not api_secret:
            raise HTTPException(
                status_code=500, 
                detail="LiveKit credentials not configured"
            )
        
        # Determine display name based on identity
        display_name = "Teacher" if identity == "teacher" else "Student"
        
        # Create access token
        token = api.AccessToken(api_key, api_secret)
        token.with_identity(identity)
        token.with_name(display_name)
        token.with_grants(api.VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
        ))
        
        jwt_token = token.to_jwt()
        
        return TokenResponse(token=jwt_token, url=livekit_url)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token generation failed: {str(e)}")


# ============ SESSION ENDPOINTS ============

@app.post("/sessions", response_model=SessionResponse)
async def create_session(request: CreateSessionRequest):
    """Create a new classroom session"""
    if not db.get_db():
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        session = SessionModel(
            room_name=request.room_name,
            student_identity=request.student_identity,
        )

        result = await db.get_db().sessions.insert_one(session.dict(by_alias=True))
        created_session = await db.get_db().sessions.find_one({"_id": result.inserted_id})

        return SessionResponse(
            id=str(created_session["_id"]),
            room_name=created_session["room_name"],
            student_identity=created_session["student_identity"],
            started_at=created_session["started_at"],
            ended_at=created_session.get("ended_at"),
            total_duration=created_session.get("total_duration"),
            total_gaps=created_session.get("total_gaps", 0),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@app.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Get a specific session by ID"""
    if not db.get_db():
        raise HTTPException(status_code=503, detail="Database not available")

    from bson import ObjectId
    try:
        session = await db.get_db().sessions.find_one({"_id": ObjectId(session_id)})
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return SessionResponse(
            id=str(session["_id"]),
            room_name=session["room_name"],
            student_identity=session["student_identity"],
            started_at=session["started_at"],
            ended_at=session.get("ended_at"),
            total_duration=session.get("total_duration"),
            total_gaps=session.get("total_gaps", 0),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")


@app.patch("/sessions/{session_id}/end")
async def end_session(session_id: str, total_duration: float):
    """Mark a session as ended"""
    if not db.get_db():
        raise HTTPException(status_code=503, detail="Database not available")

    from bson import ObjectId
    try:
        result = await db.get_db().sessions.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$set": {
                    "ended_at": datetime.utcnow(),
                    "total_duration": total_duration,
                }
            }
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Session not found")

        return {"message": "Session ended successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to end session: {str(e)}")


@app.get("/sessions", response_model=List[SessionResponse])
async def get_all_sessions(limit: int = 50, skip: int = 0):
    """Get all sessions (paginated)"""
    if not db.get_db():
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        sessions = await db.get_db().sessions.find().sort("started_at", -1).skip(skip).limit(limit).to_list(length=limit)

        return [
            SessionResponse(
                id=str(s["_id"]),
                room_name=s["room_name"],
                student_identity=s["student_identity"],
                started_at=s["started_at"],
                ended_at=s.get("ended_at"),
                total_duration=s.get("total_duration"),
                total_gaps=s.get("total_gaps", 0),
            )
            for s in sessions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sessions: {str(e)}")


# ============ GAP ENDPOINTS ============

@app.post("/gaps", response_model=GapResponse)
async def create_gap(request: CreateGapRequest):
    """Create a new attention gap"""
    if not db.get_db():
        raise HTTPException(status_code=503, detail="Database not available")

    from bson import ObjectId
    try:
        gap = GapModel(
            session_id=request.session_id,
            timestamp=request.timestamp,
            duration=request.duration,
            session_time=request.session_time,
        )

        result = await db.get_db().gaps.insert_one(gap.dict(by_alias=True))

        # Update session gap count
        await db.get_db().sessions.update_one(
            {"_id": ObjectId(request.session_id)},
            {"$inc": {"total_gaps": 1}}
        )

        created_gap = await db.get_db().gaps.find_one({"_id": result.inserted_id})

        return GapResponse(
            id=str(created_gap["_id"]),
            session_id=created_gap["session_id"],
            timestamp=created_gap["timestamp"],
            duration=created_gap["duration"],
            session_time=created_gap["session_time"],
            created_at=created_gap["created_at"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create gap: {str(e)}")


@app.get("/gaps/session/{session_id}", response_model=List[GapResponse])
async def get_gaps_for_session(session_id: str):
    """Get all gaps for a specific session"""
    if not db.get_db():
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        gaps = await db.get_db().gaps.find({"session_id": session_id}).sort("timestamp", 1).to_list(length=1000)

        return [
            GapResponse(
                id=str(g["_id"]),
                session_id=g["session_id"],
                timestamp=g["timestamp"],
                duration=g["duration"],
                session_time=g["session_time"],
                created_at=g["created_at"],
            )
            for g in gaps
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get gaps: {str(e)}")


@app.get("/gaps", response_model=List[GapResponse])
async def get_all_gaps(limit: int = 100, skip: int = 0):
    """Get all gaps (paginated)"""
    if not db.get_db():
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        gaps = await db.get_db().gaps.find().sort("timestamp", -1).skip(skip).limit(limit).to_list(length=limit)

        return [
            GapResponse(
                id=str(g["_id"]),
                session_id=g["session_id"],
                timestamp=g["timestamp"],
                duration=g["duration"],
                session_time=g["session_time"],
                created_at=g["created_at"],
            )
            for g in gaps
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get gaps: {str(e)}")


# ============ TRANSCRIPT ENDPOINTS ============

@app.post("/transcripts", response_model=TranscriptResponse)
async def create_transcript(request: CreateTranscriptRequest):
    """Store a transcript segment from the transcription agent"""
    if not db.get_db():
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        transcript = TranscriptModel(
            room_name=request.room_name,
            text=request.text,
            start_time=request.start_time,
            end_time=request.end_time,
            is_final=request.is_final,
        )

        result = await db.get_db().transcripts.insert_one(transcript.dict(by_alias=True))
        created = await db.get_db().transcripts.find_one({"_id": result.inserted_id})

        return TranscriptResponse(
            id=str(created["_id"]),
            room_name=created["room_name"],
            text=created["text"],
            start_time=created["start_time"],
            end_time=created["end_time"],
            is_final=created["is_final"],
            created_at=created["created_at"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create transcript: {str(e)}")


@app.get("/transcripts/room/{room_name}", response_model=List[TranscriptResponse])
async def get_transcripts_for_room(room_name: str, limit: int = 1000):
    """Get all transcripts for a specific room"""
    if not db.get_db():
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        transcripts = await db.get_db().transcripts.find(
            {"room_name": room_name}
        ).sort("start_time", 1).limit(limit).to_list(length=limit)

        return [
            TranscriptResponse(
                id=str(t["_id"]),
                room_name=t["room_name"],
                text=t["text"],
                start_time=t["start_time"],
                end_time=t["end_time"],
                is_final=t["is_final"],
                created_at=t["created_at"],
            )
            for t in transcripts
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get transcripts: {str(e)}")


@app.get("/transcripts/range", response_model=List[TranscriptResponse])
async def get_transcripts_in_range(room_name: str, start_time: float, end_time: float):
    """Get transcripts within a specific time range (for gap recovery)"""
    if not db.get_db():
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        # Get transcripts that overlap with the requested time range
        transcripts = await db.get_db().transcripts.find({
            "room_name": room_name,
            "$or": [
                # Transcript starts within range
                {"start_time": {"$gte": start_time, "$lte": end_time}},
                # Transcript ends within range  
                {"end_time": {"$gte": start_time, "$lte": end_time}},
                # Transcript spans the entire range
                {"$and": [{"start_time": {"$lte": start_time}}, {"end_time": {"$gte": end_time}}]}
            ]
        }).sort("start_time", 1).to_list(length=100)

        return [
            TranscriptResponse(
                id=str(t["_id"]),
                room_name=t["room_name"],
                text=t["text"],
                start_time=t["start_time"],
                end_time=t["end_time"],
                is_final=t["is_final"],
                created_at=t["created_at"],
            )
            for t in transcripts
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get transcripts: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
