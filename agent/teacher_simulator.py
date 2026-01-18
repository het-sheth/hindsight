"""
Hindsight Teacher Simulator - YouTube Audio via LiveKit

This script simulates a teacher by:
1. Downloading audio from a YouTube video
2. Publishing it to a LiveKit room as "teacher"

Students subscribe to this room and hear the lecture.
The transcription agent also subscribes and transcribes.

Usage:
    python teacher_simulator.py [youtube_url]
    
Example:
    python teacher_simulator.py "https://www.youtube.com/watch?v=8hly31xKli0"
"""

import os
import sys
import asyncio
import logging
import subprocess
import tempfile
from pathlib import Path
from dotenv import load_dotenv

from livekit import rtc, api

# Load environment variables
env_path = Path(__file__).parent.parent / ".env.local"
load_dotenv(env_path)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("teacher-simulator")

# Default YouTube video (DSA tutorial)
DEFAULT_VIDEO = "https://www.youtube.com/watch?v=8hly31xKli0"

# Audio settings
SAMPLE_RATE = 48000
NUM_CHANNELS = 1
FRAME_DURATION_MS = 20
SAMPLES_PER_FRAME = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)


async def download_audio(youtube_url: str) -> str:
    """Download audio from YouTube video using yt-dlp"""
    logger.info(f"📥 Downloading audio from: {youtube_url}")
    
    # Create temp file for audio
    temp_dir = tempfile.gettempdir()
    output_path = os.path.join(temp_dir, "hindsight_teacher_audio.wav")
    
    # Use yt-dlp to download and convert to WAV
    cmd = [
        "yt-dlp",
        "-x",  # Extract audio
        "--audio-format", "wav",
        "--audio-quality", "0",
        "-o", output_path.replace(".wav", ".%(ext)s"),
        "--postprocessor-args", f"-ar {SAMPLE_RATE} -ac {NUM_CHANNELS}",
        youtube_url,
        "--no-playlist",
        "--quiet"
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        logger.info(f"✅ Audio downloaded to: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to download audio: {e}")
        raise
    except FileNotFoundError:
        logger.error("❌ yt-dlp not found. Install with: pip install yt-dlp")
        raise


async def stream_audio_to_livekit(audio_path: str, room_name: str = "hindsight-classroom"):
    """Stream audio file to LiveKit room as teacher"""
    
    # Get LiveKit credentials
    livekit_url = os.getenv("LIVEKIT_URL", "")
    api_key = os.getenv("LIVEKIT_API_KEY", "")
    api_secret = os.getenv("LIVEKIT_API_SECRET", "")
    
    if not all([livekit_url, api_key, api_secret]):
        raise ValueError("LiveKit credentials not configured in .env.local")
    
    # Create access token for teacher
    token = api.AccessToken(api_key, api_secret)
    token.with_identity("teacher")
    token.with_name("Teacher (YouTube)")
    token.with_grants(api.VideoGrants(
        room_join=True,
        room=room_name,
        can_publish=True,
        can_subscribe=False,  # Teacher doesn't need to subscribe
    ))
    
    jwt_token = token.to_jwt()
    
    # Connect to room
    room = rtc.Room()
    
    logger.info(f"🔌 Connecting to room: {room_name}")
    await room.connect(livekit_url, jwt_token)
    logger.info("✅ Connected to LiveKit room")
    
    # Create audio source and track
    audio_source = rtc.AudioSource(SAMPLE_RATE, NUM_CHANNELS)
    track = rtc.LocalAudioTrack.create_audio_track("teacher-audio", audio_source)
    
    # Publish track
    options = rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE)
    publication = await room.local_participant.publish_track(track, options)
    logger.info(f"🎙️ Published audio track: {publication.sid}")
    
    # Read and stream audio file
    logger.info("▶️ Starting audio playback...")
    
    try:
        import wave
        with wave.open(audio_path, 'rb') as wav_file:
            # Verify audio format
            assert wav_file.getnchannels() == NUM_CHANNELS, "Audio must be mono"
            assert wav_file.getframerate() == SAMPLE_RATE, f"Audio must be {SAMPLE_RATE}Hz"
            
            frame_count = 0
            total_frames = wav_file.getnframes()
            duration_sec = total_frames / SAMPLE_RATE
            
            logger.info(f"📼 Audio duration: {duration_sec:.1f} seconds")
            
            while True:
                # Read audio data
                data = wav_file.readframes(SAMPLES_PER_FRAME)
                if not data:
                    break
                
                # Convert to audio frame
                import numpy as np
                samples = np.frombuffer(data, dtype=np.int16)
                
                if len(samples) < SAMPLES_PER_FRAME:
                    # Pad last frame if needed
                    samples = np.pad(samples, (0, SAMPLES_PER_FRAME - len(samples)))
                
                # Create and send frame
                frame = rtc.AudioFrame(
                    data=samples.tobytes(),
                    sample_rate=SAMPLE_RATE,
                    num_channels=NUM_CHANNELS,
                    samples_per_channel=SAMPLES_PER_FRAME,
                )
                await audio_source.capture_frame(frame)
                
                frame_count += 1
                
                # Log progress every 5 seconds
                if frame_count % (5000 // FRAME_DURATION_MS) == 0:
                    elapsed = frame_count * FRAME_DURATION_MS / 1000
                    logger.info(f"⏱️ Streamed {elapsed:.0f}s / {duration_sec:.0f}s")
                
                # Wait for frame duration to maintain real-time playback
                await asyncio.sleep(FRAME_DURATION_MS / 1000)
        
        logger.info("✅ Audio playback complete!")
        
    except Exception as e:
        logger.error(f"❌ Error streaming audio: {e}")
        raise
    finally:
        await room.disconnect()
        logger.info("🔌 Disconnected from room")


async def main():
    # Get YouTube URL from command line or use default
    youtube_url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_VIDEO
    room_name = sys.argv[2] if len(sys.argv) > 2 else "hindsight-classroom"
    
    logger.info("=" * 50)
    logger.info("🎓 Hindsight Teacher Simulator")
    logger.info("=" * 50)
    logger.info(f"📺 YouTube Video: {youtube_url}")
    logger.info(f"🏫 Room: {room_name}")
    logger.info("")
    
    # Download audio
    audio_path = await download_audio(youtube_url)
    
    # Stream to LiveKit
    await stream_audio_to_livekit(audio_path, room_name)


if __name__ == "__main__":
    asyncio.run(main())
