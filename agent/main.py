"""
Hindsight Recovery Agent - LiveKit Voice Assistant with Transcript Context

This agent helps students recover context when they've been distracted.
It receives transcript information for the missed period and explains
what was discussed.

Uses:
- OpenRouter (Gemini 2.0 Flash) for LLM
- Deepgram for STT
- ElevenLabs (eleven_turbo_v2_5) for TTS

Usage:
    python recovery_agent.py dev
"""

import os
import asyncio
import logging
import aiohttp
from pathlib import Path
from dotenv import load_dotenv

from livekit import agents, rtc
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.plugins import deepgram, elevenlabs, openai

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
                        # Combine all transcript segments
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


def create_system_prompt(transcript: str = "", gap_duration: float = 0) -> str:
    """Create a context-aware system prompt for the recovery agent"""
    
    base_prompt = """You are Hindsight, an AI teaching assistant designed to help students recover context when they've been distracted.

Your role:
1. The student looked away from an educational video and missed some content
2. You need to help them understand what they missed
3. Be warm, encouraging, and non-judgmental about the distraction
4. Provide concise but helpful explanations
5. Ask if they have any questions about the missed content

Speaking style:
- Keep responses brief (2-3 sentences max for initial greeting)
- Speak conversationally, like a friendly tutor
- Be encouraging and supportive
- Don't lecture - engage in dialogue
"""
    
    if transcript:
        context_prompt = f"""

IMPORTANT CONTEXT - Here is what was discussed while the student was away (approximately {gap_duration:.0f} seconds of content):

---
{transcript}
---

Use this context to explain what the student missed. Summarize the key points naturally in conversation.
Start by briefly mentioning what topic was being discussed, then ask if they'd like more details."""
        return base_prompt + context_prompt
    else:
        return base_prompt + """

Note: No transcript is available for the missed period. Acknowledge this and offer to help the student 
catch up by discussing the general topic or answering questions about the material."""


async def entrypoint(ctx: JobContext):
    """
    Main entrypoint for the Hindsight recovery voice agent.
    """
    logger.info(f"🧠 Recovery agent connecting to room: {ctx.room.name}")
    
    # Connect to the room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    # Wait for a participant to join
    participant = await ctx.wait_for_participant()
    logger.info(f"👤 Student joined: {participant.identity}")
    
    # Try to get gap context from room metadata
    # Room name format: recovery-{gap_id}
    # We'll also check room metadata for gap details
    transcript = ""
    gap_duration = 0
    
    # Parse room metadata if available
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
                logger.info(f"📍 Gap context: {start_time:.1f}s - {end_time:.1f}s ({gap_duration:.1f}s)")
                transcript = await fetch_transcript_for_gap(classroom_room, start_time, end_time)
        except Exception as e:
            logger.warning(f"⚠️ Could not parse room metadata: {e}")
    
    # Create system prompt with transcript context
    system_prompt = create_system_prompt(transcript, gap_duration)
    
    # Configure OpenRouter LLM (using OpenAI-compatible plugin)
    openrouter_llm = openai.LLM(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        model="google/gemini-2.0-flash-001",
    )
    
    # Create and start the voice assistant
    assistant = agents.VoiceAssistant(
        vad=agents.silero.VAD.load(),
        stt=deepgram.STT(),
        llm=openrouter_llm,
        tts=elevenlabs.TTS(model="eleven_turbo_v2_5"),
        chat_ctx=llm.ChatContext().append(
            role="system",
            text=system_prompt
        ),
    )
    
    # Start the agent
    assistant.start(ctx.room, participant)
    
    if transcript:
        logger.info(f"🎯 Agent started with {len(transcript)} chars of transcript context")
    else:
        logger.info("🎯 Agent started without transcript context")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
