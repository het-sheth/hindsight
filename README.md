# Hindsight

A voice-AI teaching assistant that catches distracted students back up on what
they missed during a lecture.

## The idea

Everyone zones out in lectures. Hindsight watches for the moment you step away,
remembers what was covered while you were gone, and — when you come back — a
voice agent gives you a quick spoken recap so you can rejoin without losing the
thread.

## How it works

1. A lecture is transcribed in real time (for demos, a **teacher simulator**
   streams YouTube lecture audio into a LiveKit "classroom" room).
2. When a student steps away, Hindsight records the **gap** — its duration and
   the transcript of everything discussed during it.
3. When the student returns, they join a `recovery-` room. A **LiveKit voice
   agent** receives the gap transcript and duration as context, then summarizes
   what was missed and answers follow-up questions by voice.

## Architecture

| Component | Role | Tech |
|-----------|------|------|
| **Voice agent** | Joins `recovery-` rooms, recaps the missed window, handles voice Q&A | LiveKit Agents · Deepgram (STT) · OpenAI (LLM) · ElevenLabs (TTS) · Silero (VAD) |
| **Backend** | Stores gap records, serves transcript/context to the agent | FastAPI · MongoDB Atlas (Motor async) · Pydantic v2 |
| **Frontend** | Student-facing UI | Next.js 16 · React 19 |
| **Teacher simulator** | Streams YouTube lecture audio into a classroom room for demos | LiveKit |

## Documentation

- [`QUICKSTART.md`](QUICKSTART.md) — get running with MongoDB Atlas in ~10 minutes
- [`MONGODB_SETUP.md`](MONGODB_SETUP.md) — database configuration
- [`API_REFERENCE.md`](API_REFERENCE.md) — backend API

## Status

Built as a hackathon project — a working demo of voice-driven lecture context
recovery.
