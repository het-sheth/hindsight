"""
Hindsight Transcription Agent - LiveKit Audio Transcription

This agent joins the classroom room, subscribes to teacher's audio,
and transcribes it using Deepgram STT. Transcripts are stored in MongoDB
via the backend API for context recovery.

Usage:
    python transcription_agent.py dev
"""

import os
import asyncio
import logging
import time
import aiohttp
from pathlib import Path
from dotenv import load_dotenv

from livekit import agents, rtc
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli
from livekit.plugins import deepgram

# Load environment variables
env_path = Path(__file__).parent.parent / ".env.local"
load_dotenv(env_path)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("transcription-agent")

# Backend API URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


class TranscriptionHandler:
    """Handles real-time transcription and storage"""
    
    def __init__(self, room_name: str):
        self.room_name = room_name
        self.session_start = time.time()
        self.current_segment_start = 0.0
        
    async def store_transcript(self, text: str, start_time: float, end_time: float, is_final: bool = True):
        """Store transcript segment to MongoDB via backend API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{API_BASE_URL}/transcripts",
                    json={
                        "room_name": self.room_name,
                        "text": text,
                        "start_time": start_time,
                        "end_time": end_time,
                        "is_final": is_final,
                    }
                ) as response:
                    if response.status == 200:
                        logger.info(f"✅ Stored transcript: {text[:50]}...")
                    else:
                        logger.warning(f"⚠️ Failed to store transcript: {response.status}")
        except Exception as e:
            logger.error(f"❌ Error storing transcript: {e}")


async def entrypoint(ctx: JobContext):
    """
    Main entrypoint for the transcription agent.
    Joins the classroom room and transcribes teacher audio.
    """
    logger.info(f"🎤 Transcription agent connecting to room: {ctx.room.name}")
    
    # Connect to the room - subscribe to audio only
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    # Initialize transcription handler
    handler = TranscriptionHandler(ctx.room.name)
    session_start_time = time.time()
    
    # Create Deepgram STT
    stt = deepgram.STT()
    
    logger.info("⏳ Waiting for participants with audio...")
    
    # Track active transcription streams
    transcription_tasks = {}
    
    async def handle_track(track: rtc.Track, participant: rtc.RemoteParticipant):
        """Handle incoming audio track and transcribe it"""
        if track.kind != rtc.TrackKind.KIND_AUDIO:
            return
            
        # Skip if this is the student (we only want teacher audio)
        if "student" in participant.identity.lower():
            logger.info(f"⏭️ Skipping student audio: {participant.identity}")
            return
            
        logger.info(f"🎙️ Transcribing audio from: {participant.identity}")
        
        # Create audio stream from track
        audio_stream = rtc.AudioStream(track)
        
        # Create STT stream
        stt_stream = stt.stream()
        
        # Track current transcription segment
        segment_start = time.time() - session_start_time
        accumulated_text = ""
        
        async def process_stt_events():
            nonlocal accumulated_text, segment_start
            
            async for event in stt_stream:
                if event.type == agents.stt.SpeechEventType.INTERIM_TRANSCRIPT:
                    # Log interim results but don't store
                    if event.alternatives:
                        text = event.alternatives[0].text
                        logger.debug(f"📝 Interim: {text}")
                        
                elif event.type == agents.stt.SpeechEventType.FINAL_TRANSCRIPT:
                    if event.alternatives:
                        text = event.alternatives[0].text
                        if text.strip():
                            end_time = time.time() - session_start_time
                            logger.info(f"✅ Final: {text}")
                            
                            # Store the transcript
                            await handler.store_transcript(
                                text=text,
                                start_time=segment_start,
                                end_time=end_time,
                                is_final=True
                            )
                            
                            # Reset for next segment
                            segment_start = end_time
                            
                elif event.type == agents.stt.SpeechEventType.END_OF_SPEECH:
                    logger.debug("🔇 End of speech detected")
                    segment_start = time.time() - session_start_time
        
        # Start processing STT events
        stt_task = asyncio.create_task(process_stt_events())
        
        # Forward audio frames to STT
        async for frame_event in audio_stream:
            stt_stream.push_frame(frame_event.frame)
        
        # Cleanup
        await stt_stream.aclose()
        stt_task.cancel()
        logger.info(f"🔴 Audio track ended from: {participant.identity}")
    
    # Handle existing tracks
    for participant in ctx.room.remote_participants.values():
        for track_pub in participant.track_publications.values():
            if track_pub.track and track_pub.kind == rtc.TrackKind.KIND_AUDIO:
                asyncio.create_task(handle_track(track_pub.track, participant))
    
    # Handle new tracks
    @ctx.room.on("track_subscribed")
    def on_track_subscribed(track: rtc.Track, publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
        if track.kind == rtc.TrackKind.KIND_AUDIO:
            asyncio.create_task(handle_track(track, participant))
    
    logger.info("🎤 Transcription agent ready and listening!")
    
    # Keep the agent running
    while ctx.room.connection_state == rtc.ConnectionState.CONN_CONNECTED:
        await asyncio.sleep(1)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
