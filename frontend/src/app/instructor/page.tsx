"use client";

import { useState, useEffect } from "react";
import {
  LiveKitRoom,
  VideoConference,
  RoomAudioRenderer,
} from "@livekit/components-react";
import "@livekit/components-styles";

const API_BASE_URL = "http://localhost:8000";

export default function InstructorPage() {
  const [tokenData, setTokenData] = useState<{ token: string; url: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [roomName] = useState("hindsight-classroom");

  useEffect(() => {
    const fetchToken = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/token?room_name=${roomName}`);
        const data = await res.json();
        setTokenData(data);
      } catch (err: any) {
        setError(err.message);
      }
    };

    fetchToken();
  }, [roomName]);

  if (error) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <div className="text-center p-8">
          <div className="text-red-400 text-lg mb-2">Connection Error</div>
          <div className="text-zinc-500 text-sm">{error}</div>
        </div>
      </div>
    );
  }

  if (!tokenData) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <div className="flex items-center gap-3">
          <div className="animate-spin rounded-full h-6 w-6 border-2 border-violet-500 border-t-transparent" />
          <span className="text-zinc-400">Connecting to classroom...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-950 via-zinc-900 to-zinc-950">
      <div className="max-w-7xl mx-auto px-6 py-8">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-violet-400 via-cyan-400 to-violet-400 bg-clip-text text-transparent mb-2">
            Hindsight - Instructor View
          </h1>
          <p className="text-zinc-400">Teaching in room: {roomName}</p>
        </header>

        <div className="rounded-2xl overflow-hidden bg-zinc-900 border border-zinc-800 shadow-2xl">
          <LiveKitRoom
            token={tokenData.token}
            serverUrl={tokenData.url}
            connect={true}
            audio={true}
            video={true}
            className="h-[80vh]"
          >
            <VideoConference />
            <RoomAudioRenderer />
          </LiveKitRoom>
        </div>

        <div className="mt-6 p-4 rounded-xl bg-zinc-900/50 border border-zinc-800">
          <h3 className="text-sm font-semibold text-zinc-300 mb-2">Instructions:</h3>
          <ul className="text-xs text-zinc-500 space-y-1">
            <li>• Your camera and microphone are now live in the classroom</li>
            <li>• Students will see your video feed in real-time</li>
            <li>• Hindsight AI monitors student attention and helps them catch up when distracted</li>
            <li>• You can share your screen using the screen share button below</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
