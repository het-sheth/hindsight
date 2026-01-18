"""
Hindsight Recovery Agent - LiveKit Voice Assistant

This agent helps students recover context when they've been distracted.

Usage:
    python main.py dev
"""

import os
import logging
import aiohttp
from pathlib import Path
from dotenv import load_dotenv

from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
)
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import deepgram, openai, silero, elevenlabs

# Load environment variables
env_path = Path(__file__).parent.parent / ".env.local"
load_dotenv(env_path)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hindsight-agent")

# Backend API URL  
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


async def fetch_transcript_for_gap(room_name: str, start_time: float, end_time: float) -> str:
    """Fetch transcript segments for the time period the student missed"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{API_BASE_URL}/transcripts/range"
            params = {
                "room_name": room_name,
                "start_time": start_time,
                "end_time": end_time
            }
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    transcripts = await response.json()
                    if transcripts:
                        full_text = " ".join([t["text"] for t in transcripts])
                        logger.info(f"📝 Fetched {len(transcripts)} transcript segments")
                        return full_text
                    else:
                        logger.info("📝 No transcripts found for this time range")
                        return ""
                else:
                    logger.warning(f"⚠️ Failed to fetch transcripts: {response.status}")
                    return ""
    except Exception as e:
        logger.error(f"❌ Error fetching transcripts: {e}")
        return ""


def create_instructions(transcript: str = "", gap_duration: float = 0) -> str:
    """Create context-aware instructions for the recovery agent"""
    
    base = """You are Hindsight, an AI teaching assistant that helps students recover context when distracted during a lecture.

Your role:
- Help students understand what they missed
- Be warm, encouraging, and non-judgmental
- Provide concise explanations
- Ask if they have questions

Speaking style:
- Brief responses (2-3 sentences)
- Conversational, like a friendly tutor
- Encouraging and supportive
"""
    
    if transcript:
        return base + f"""

CONTEXT - What was discussed while they were away ({gap_duration:.0f} seconds):

---
{transcript}
---

Summarize key points naturally. Start with the topic, ask if they want details."""
    else:
        return base + """

Note: No transcript available. Offer to discuss the topic or answer questions."""


class HindsightAgent(Agent):
    """Voice agent that helps students recover missed content"""
    
    def __init__(self, instructions: str) -> None:
        super().__init__(instructions=instructions)


async def entrypoint(ctx: JobContext):
    """Main entrypoint for the Hindsight recovery voice agent."""
    # Only handle recovery rooms (not classroom rooms)
    if not ctx.room.name.startswith("recovery-"):
        logger.info(f"⏭️ Skipping non-recovery room: {ctx.room.name}")
        return

    logger.info(f"🧠 Recovery agent connecting to room: {ctx.room.name}")

    # Connect to the room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    # Wait for participant
    participant = await ctx.wait_for_participant()
    logger.info(f"👤 Student joined: {participant.identity}")
    
    # Get gap context from room metadata
    transcript = ""
    gap_duration = 0
    
    room_metadata = ctx.room.metadata or ""
    if room_metadata:
        try:
            import json
            metadata = json.loads(room_metadata)
            classroom_room = metadata.get("classroom_room", "hindsight-classroom")
            start_time = metadata.get("gap_start_time", 0)
            end_time = metadata.get("gap_end_time", 0)
            gap_duration = end_time - start_time
            
            if start_time and end_time:
                logger.info(f"📍 Gap: {start_time:.1f}s - {end_time:.1f}s ({gap_duration:.1f}s)")
                transcript = await fetch_transcript_for_gap(classroom_room, start_time, end_time)
        except Exception as e:
            logger.warning(f"⚠️ Could not parse room metadata: {e}")
    
    instructions = create_instructions(transcript, gap_duration)
    
    # Create session with STT-LLM-TTS pipeline
    session = AgentSession(
        stt=deepgram.STT(),
        llm=openai.LLM(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            model="google/gemini-2.0-flash-001",
        ),
        tts=elevenlabs.TTS(api_key=os.getenv("ELEVENLABS_API_KEY")),
        vad=silero.VAD.load(),
    )
    
    # Start session
    await session.start(
        room=ctx.room,
        agent=HindsightAgent(instructions=instructions),
    )
    
    if transcript:
        logger.info(f"🎯 Agent started with {len(transcript)} chars of context")
    else:
        logger.info("🎯 Agent started without transcript context")
    
    # Generate initial greeting
    await session.generate_reply(
        instructions="Greet the student warmly. Say 'Hi! I'm Hindsight. I noticed you looked away for a bit. Would you like me to catch you up?' Keep it brief."
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
