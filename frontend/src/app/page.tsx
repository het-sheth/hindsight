"use client";

import { useRef, useCallback, useEffect, useState } from "react";
import Webcam from "react-webcam";
import { RealtimeVision } from "@overshoot/sdk";
import {
  LiveKitRoom,
  RoomAudioRenderer,
  useVoiceAssistant,
  BarVisualizer,
  VoiceAssistantControlBar,
  VideoTrack,
  useTracks,
  useRoomContext,
  TrackLoop,
  ParticipantTile,
  GridLayout,
} from "@livekit/components-react";
import "@livekit/components-styles";
import { Track } from "livekit-client";

// ============ TYPES ============
interface Gap {
  id: string;
  timestamp: Date;
  duration: number;
  sessionTime: number; // Seconds since joining the classroom
}

interface LiveKitToken {
  token: string;
  url: string;
}

interface Session {
  id: string;
  room_name: string;
  student_identity: string;
  started_at: string;
  ended_at?: string;
  total_duration?: number;
  total_gaps: number;
}

const API_BASE_URL = "http://localhost:8000";

// ============ CLASSROOM VIDEO COMPONENT ============
function ClassroomVideo() {
  // Show live instructor video from LiveKit room
  const tracks = useTracks(
    [
      { source: Track.Source.Camera, withPlaceholder: true },
      { source: Track.Source.ScreenShare, withPlaceholder: false },
    ],
    { onlySubscribed: false }
  );

  // Filter to show only remote participants (instructor), not local student
  const instructorTracks = tracks.filter(
    (trackRef) => trackRef.participant.identity !== "student-user"
  );

  if (instructorTracks.length === 0) {
    // No instructor joined yet - show waiting state
    return (
      <div className="h-full w-full flex items-center justify-center bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-900">
        <div className="text-center p-8">
          <div className="text-6xl mb-4">👨‍🏫</div>
          <h3 className="text-xl font-semibold text-zinc-100 mb-2">
            Waiting for Instructor
          </h3>
          <p className="text-zinc-400 text-sm mb-4">
            The instructor will appear here when they join the classroom.
          </p>
          <div className="flex items-center justify-center gap-2 text-zinc-500 text-xs">
            <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
            Listening for instructor...
          </div>
        </div>
      </div>
    );
  }

  return (
    <GridLayout tracks={instructorTracks} className="h-full w-full">
      <ParticipantTile />
    </GridLayout>
  );
}

// ============ CLASSROOM COMPONENT ============
// Simple YouTube video for demo - press 'L' to simulate looking away
const DEMO_VIDEO_ID = "8hly31xKli0"; // Data Structures Full Course

function Classroom({
  onTimeUpdate,
  roomName,
  onSessionCreated,
}: {
  onTimeUpdate: (time: number) => void;
  roomName: string;
  onSessionCreated: (sessionId: string) => void;
}) {
  const [sessionStart] = useState<number>(Date.now());
  const [sessionId, setSessionId] = useState<string | null>(null);

  // Create session on mount
  useEffect(() => {
    const initSession = async () => {
      try {
        const sessionRes = await fetch(`${API_BASE_URL}/sessions`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            room_name: roomName,
            student_identity: "student-user",
          }),
        });
        const session = await sessionRes.json();
        setSessionId(session.id);
        onSessionCreated(session.id);
        console.log("✅ Session created:", session.id);
      } catch (err) {
        console.warn("⚠️ Could not create session:", err);
      }
    };

    initSession();
  }, [roomName, onSessionCreated]);

  // Track session time
  useEffect(() => {
    const interval = setInterval(() => {
      onTimeUpdate((Date.now() - sessionStart) / 1000);
    }, 1000);
    return () => clearInterval(interval);
  }, [sessionStart, onTimeUpdate]);

  return (
    <div className="aspect-video w-full rounded-2xl overflow-hidden bg-zinc-900 border border-zinc-800 shadow-2xl relative">
      {/* YouTube Video */}
      <iframe
        src={`https://www.youtube.com/embed/${DEMO_VIDEO_ID}?autoplay=1&cc_load_policy=1`}
        title="DSA Lecture"
        className="w-full h-full"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowFullScreen
      />

      {/* Status badge */}
      <div className="absolute top-4 left-4 z-10">
        <div className="px-3 py-1.5 rounded-full text-xs font-medium backdrop-blur-sm bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
          🎓 Watching Lecture
        </div>
      </div>

      {/* Info badge */}
      <div className="absolute bottom-4 left-4 z-10">
        <div className="px-2 py-1 rounded text-[10px] font-medium bg-zinc-800/90 text-zinc-400 backdrop-blur-sm">
          Press 'L' to simulate looking away
        </div>
      </div>
    </div>
  );
}

// ============ WAITING ROOM (when no meeting is active) ============
function WaitingRoom() {
  return (
    <div className="aspect-video w-full rounded-2xl overflow-hidden bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-900 border border-zinc-700 shadow-2xl flex items-center justify-center">
      <div className="text-center p-8 max-w-md">
        <div className="text-6xl mb-4">📚</div>
        <h2 className="text-xl font-semibold text-zinc-100 mb-2">
          Waiting for Class
        </h2>
        <p className="text-zinc-400 text-sm mb-4">
          The classroom will appear here when the instructor starts the session.
        </p>
        <div className="flex items-center justify-center gap-2 text-zinc-500 text-xs">
          <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
          Listening for instructor...
        </div>
      </div>
    </div>
  );
}

// ============ ATTENTION TRACKER COMPONENT ============
function AttentionTracker({
  onDistractionStart,
  onDistractionEnd,
  currentSessionTime,
}: {
  onDistractionStart: (sessionTime: number) => void;
  onDistractionEnd: () => void;
  currentSessionTime: number;
}) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const visionRef = useRef<RealtimeVision | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isFocused, setIsFocused] = useState(true);
  const [lastResult, setLastResult] = useState<any>(null);
  const [showDebug, setShowDebug] = useState(false);
  const distractionStartRef = useRef<number | null>(null);

  // Toggle debug with 'd' key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "d") setShowDebug((prev) => !prev);
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);
  const currentSessionTimeRef = useRef(currentSessionTime);

  // Keep session time ref updated
  useEffect(() => {
    currentSessionTimeRef.current = currentSessionTime;
  }, [currentSessionTime]);

  // Initialize webcam (demo mode - press 'L' to toggle focus)
  useEffect(() => {
    const initWebcam = async () => {
      try {
        // Get user media for webcam preview
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "user", width: 320, height: 240 },
          audio: false,
        });

        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
        }

        setIsLoading(false);
        console.log("📹 Webcam initialized - Press 'L' to simulate looking away");
      } catch (error) {
        console.error("Failed to initialize webcam:", error);
        setIsLoading(false);
      }
    };

    // Demo keyboard control: Press 'L' to toggle focus state
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "l" || e.key === "L") {
        setIsFocused(prev => {
          const newFocused = !prev;

          if (!newFocused && !distractionStartRef.current) {
            // Started looking away
            distractionStartRef.current = currentSessionTimeRef.current;
            onDistractionStart(currentSessionTimeRef.current);
            console.log("⚠️ [DEMO] Simulating distraction - looking away");
            setLastResult({ is_focused: false, confidence: 0.85, reason: "Demo: Looking away" });
          } else if (newFocused && distractionStartRef.current) {
            // Looking back
            distractionStartRef.current = null;
            onDistractionEnd();
            console.log("✅ [DEMO] Simulating focus restored - looking back");
            setLastResult({ is_focused: true, confidence: 0.92, reason: "Demo: Looking at screen" });
          }

          return newFocused;
        });
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    initWebcam();

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      if (videoRef.current?.srcObject) {
        const tracks = (videoRef.current.srcObject as MediaStream).getTracks();
        tracks.forEach((track) => track.stop());
      }
    };
  }, [onDistractionStart, onDistractionEnd]);

  return (
    <div className="relative">
      {/* Webcam preview */}
      <div className="absolute bottom-4 right-4 w-32 h-24 rounded-xl overflow-hidden border-2 border-zinc-700 shadow-lg z-10 group">
        <video
          ref={videoRef}
          muted
          playsInline
          className="w-full h-full object-cover"
          style={{ transform: "scaleX(-1)" }}
        />
        <div
          className={`absolute inset-0 transition-colors ${isLoading
            ? "bg-zinc-900/80"
            : isFocused
              ? "bg-emerald-500/10"
              : "bg-red-500/20"
            }`}
        />

        {/* Debug Overlay - Toggle with 'd' */}
        {showDebug && lastResult && (
          <div className="absolute inset-0 bg-black/80 p-2 text-[8px] text-green-400 font-mono overflow-auto z-20">
            <pre>{JSON.stringify(lastResult, null, 2)}</pre>
          </div>
        )}

        <div className="absolute bottom-1 left-1/2 -translate-x-1/2">
          <div
            className={`w-2 h-2 rounded-full ${isLoading
              ? "bg-zinc-500"
              : isFocused
                ? "bg-emerald-500 shadow-lg shadow-emerald-500/50"
                : "bg-red-500 animate-pulse shadow-lg shadow-red-500/50"
              }`}
          />
        </div>

      </div>

      {/* Status text */}
      <div className="absolute top-4 right-4 z-10">
        <div
          className={`px-3 py-1.5 rounded-full text-xs font-medium backdrop-blur-sm ${isLoading
            ? "bg-zinc-800/80 text-zinc-400"
            : isFocused
              ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
              : "bg-red-500/20 text-red-400 border border-red-500/30 animate-pulse"
            }`}
        >
          {isLoading
            ? "🔄 Loading Overshoot..."
            : isFocused
              ? `👀 Focused (${Math.round((lastResult?.confidence || 0) * 100)}%)`
              : "⚠️ Look at screen!"}
        </div>
      </div>

      {/* Overshoot branding */}
      <div className="absolute bottom-4 left-4 z-10">
        <div className="px-2 py-1 rounded text-[10px] font-medium bg-zinc-800/80 text-zinc-500 backdrop-blur-sm">
          Powered by Overshoot
        </div>
      </div>
    </div>
  );
}

// ============ STATS PANEL COMPONENT ============
function StatsPanel({ gaps, sessionTime }: { gaps: Gap[]; sessionTime: number }) {
  const totalTimeLost = gaps.reduce((acc, gap) => acc + gap.duration, 0);
  const avgGapDuration = gaps.length > 0 ? totalTimeLost / gaps.length : 0;
  const focusPercentage = sessionTime > 0
    ? Math.max(0, Math.min(100, ((sessionTime - totalTimeLost) / sessionTime) * 100))
    : 100;

  return (
    <div className="grid grid-cols-2 gap-2 mb-4">
      <div className="p-3 rounded-xl bg-zinc-900/50 border border-zinc-800/50">
        <div className="text-2xl font-bold text-amber-400">{gaps.length}</div>
        <div className="text-xs text-zinc-500">Gaps</div>
      </div>
      <div className="p-3 rounded-xl bg-zinc-900/50 border border-zinc-800/50">
        <div className="text-2xl font-bold text-red-400">{totalTimeLost.toFixed(0)}s</div>
        <div className="text-xs text-zinc-500">Time Lost</div>
      </div>
      <div className="p-3 rounded-xl bg-zinc-900/50 border border-zinc-800/50">
        <div className="text-2xl font-bold text-violet-400">{avgGapDuration.toFixed(1)}s</div>
        <div className="text-xs text-zinc-500">Avg Gap</div>
      </div>
      <div className="p-3 rounded-xl bg-zinc-900/50 border border-zinc-800/50">
        <div className={`text-2xl font-bold ${focusPercentage >= 80 ? 'text-emerald-400' : focusPercentage >= 50 ? 'text-amber-400' : 'text-red-400'}`}>
          {focusPercentage.toFixed(0)}%
        </div>
        <div className="text-xs text-zinc-500">Focus</div>
      </div>
    </div>
  );
}

// ============ TIMELINE COMPONENT ============
function Timeline({
  gaps,
  onGapClick,
  sessionTime,
}: {
  gaps: Gap[];
  onGapClick: (gap: Gap) => void;
  sessionTime: number;
}) {
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <div className="space-y-3">
      <StatsPanel gaps={gaps} sessionTime={sessionTime} />

      <h2 className="text-lg font-semibold text-zinc-100 flex items-center gap-2">
        <span className="text-xl">📚</span> Missed Context
        {gaps.length > 0 && (
          <span className="ml-2 px-2 py-0.5 text-xs rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/30">
            {gaps.length} gap{gaps.length > 1 ? "s" : ""}
          </span>
        )}
      </h2>

      {gaps.length === 0 ? (
        <div className="p-6 text-center rounded-xl bg-zinc-900/30 border border-zinc-800/50">
          <div className="text-zinc-500 text-sm">
            No gaps detected. Keep watching! 🎯
          </div>
        </div>
      ) : (
        <div className="space-y-2 max-h-48 overflow-y-auto">
          {gaps.map((gap) => (
            <button
              key={gap.id}
              onClick={() => onGapClick(gap)}
              className="w-full p-3 rounded-xl bg-gradient-to-r from-zinc-900/80 to-zinc-800/50
                         border border-zinc-700/50 hover:border-violet-500/50
                         transition-all duration-300 hover:shadow-lg hover:shadow-violet-500/10
                         text-left group"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-amber-500/20 flex items-center justify-center text-amber-400">
                    ⏱️
                  </div>
                  <div>
                    <div className="text-sm font-medium text-zinc-200">
                      Session @ {formatTime(gap.sessionTime)}
                    </div>
                    <div className="text-xs text-zinc-500">
                      {gap.duration.toFixed(1)}s missed
                    </div>
                  </div>
                </div>
                <span
                  className="text-xs px-3 py-1.5 rounded-full bg-violet-500/20 text-violet-300
                             group-hover:bg-violet-500/30 transition-colors font-medium"
                >
                  Ask Hindsight →
                </span>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// ============ VOICE ASSISTANT COMPONENT ============
function VoiceAssistant() {
  const { state, audioTrack } = useVoiceAssistant();

  return (
    <div className="flex flex-col items-center gap-4">
      <BarVisualizer
        state={state}
        barCount={7}
        trackRef={audioTrack}
        className="h-16"
      />
      <div className="text-sm text-zinc-400">
        {state === "listening" && "🎤 Listening..."}
        {state === "thinking" && "🧠 Thinking..."}
        {state === "speaking" && "🗣️ Speaking..."}
        {state === "idle" && "Ready to help"}
      </div>
      <VoiceAssistantControlBar />
    </div>
  );
}

// ============ RECOVERY MODE MODAL ============
function RecoveryMode({
  isOpen,
  onClose,
  gap,
  roomName,
}: {
  isOpen: boolean;
  onClose: () => void;
  gap: Gap | null;
  roomName: string;
}) {
  const [tokenData, setTokenData] = useState<LiveKitToken | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [missedTranscript, setMissedTranscript] = useState<string>("");
  const [loadingTranscript, setLoadingTranscript] = useState(false);

  useEffect(() => {
    if (isOpen && gap) {
      const startTime = gap.sessionTime;
      const endTime = gap.sessionTime + gap.duration;

      // Start recovery session - creates room with metadata for agent
      fetch(`${API_BASE_URL}/recovery/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          gap_id: gap.id,
          classroom_room: roomName,
          gap_start_time: startTime,
          gap_end_time: endTime,
        }),
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.token && data.url) {
            setTokenData({ token: data.token, url: data.url });
            console.log("✅ Recovery room created:", data.room_name);
          } else {
            setError(data.detail || "Failed to start recovery");
          }
        })
        .catch((err) => setError(err.message));

      // Fetch the transcript for the missed time period
      setLoadingTranscript(true);
      fetch(`${API_BASE_URL}/transcripts/range?room_name=${roomName}&start_time=${startTime}&end_time=${endTime}`)
        .then((res) => res.json())
        .then((data) => {
          if (data && data.length > 0) {
            const fullText = data.map((t: any) => t.text).join(" ");
            setMissedTranscript(fullText);
          }
          setLoadingTranscript(false);
        })
        .catch((err) => {
          console.warn("Could not fetch missed transcript:", err);
          setLoadingTranscript(false);
        });
    }
    return () => {
      setTokenData(null);
      setError(null);
      setMissedTranscript("");
    };
  }, [isOpen, gap, roomName]);

  if (!isOpen || !gap) return null;

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
      <div className="w-full max-w-2xl p-6 rounded-2xl bg-zinc-900 border border-zinc-700 shadow-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-semibold text-zinc-100 flex items-center gap-2">
            <span className="text-2xl">🧠</span> Hindsight Recovery
          </h3>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-zinc-800 transition-colors"
          >
            <svg className="w-5 h-5 text-zinc-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="space-y-4">
          <div className="p-4 rounded-xl bg-zinc-800/50 border border-zinc-700/50">
            <div className="text-sm text-zinc-400 mb-1">📍 You missed content at</div>
            <div className="text-lg font-semibold text-zinc-200">
              Session time: {formatTime(gap.sessionTime)}
            </div>
            <div className="text-sm text-zinc-500">
              Duration: {gap.duration.toFixed(1)} seconds
            </div>
          </div>

          {/* Missed Transcript Display */}
          <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30">
            <div className="text-sm font-medium text-amber-400 mb-2">📝 What You Missed:</div>
            {loadingTranscript ? (
              <div className="flex items-center gap-2 text-zinc-400 text-sm">
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-amber-500 border-t-transparent" />
                Loading transcript...
              </div>
            ) : missedTranscript ? (
              <p className="text-zinc-300 text-sm leading-relaxed">{missedTranscript}</p>
            ) : (
              <p className="text-zinc-500 text-sm italic">
                No transcript available for this time period. The teacher may not have been speaking.
              </p>
            )}
          </div>

          {error && (
            <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
              Error connecting: {error}
            </div>
          )}

          {tokenData ? (
            <LiveKitRoom
              token={tokenData.token}
              serverUrl={tokenData.url}
              connect={true}
              audio={true}
              video={false}
              className="p-4 rounded-xl bg-violet-500/10 border border-violet-500/30"
            >
              <VoiceAssistant />
              <RoomAudioRenderer />
            </LiveKitRoom>
          ) : !error ? (
            <div className="p-4 rounded-xl bg-violet-500/10 border border-violet-500/30 flex items-center justify-center">
              <div className="animate-spin rounded-full h-6 w-6 border-2 border-violet-500 border-t-transparent" />
              <span className="ml-3 text-violet-300">Connecting to Hindsight AI...</span>
            </div>
          ) : null}

          <p className="text-xs text-zinc-500 text-center">
            Talk to Hindsight to get more details about what you missed.
          </p>
        </div>
      </div>
    </div>
  );
}

// ============ MAIN PAGE ============
export default function Home() {
  const [gaps, setGaps] = useState<Gap[]>([]);
  const [selectedGap, setSelectedGap] = useState<Gap | null>(null);
  const [isRecoveryOpen, setIsRecoveryOpen] = useState(false);
  const [currentSessionTime, setCurrentSessionTime] = useState(0);
  const [classroomRoom] = useState("hindsight-classroom");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const distractionStartTime = useRef<{ session: number; real: Date } | null>(null);

  const handleSessionCreated = useCallback((id: string) => {
    setSessionId(id);
  }, []);

  const handleDistractionStart = useCallback((sessionTime: number) => {
    distractionStartTime.current = { session: sessionTime, real: new Date() };
  }, []);

  const handleDistractionEnd = useCallback(async () => {
    if (distractionStartTime.current) {
      const gap: Gap = {
        id: crypto.randomUUID(),
        timestamp: distractionStartTime.current.real,
        duration: (new Date().getTime() - distractionStartTime.current.real.getTime()) / 1000,
        sessionTime: distractionStartTime.current.session,
      };

      // Only log gaps longer than 2 seconds
      if (gap.duration > 2) {
        setGaps((prev) => [gap, ...prev]);

        // Persist to MongoDB if session exists
        if (sessionId) {
          try {
            await fetch(`${API_BASE_URL}/gaps`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                session_id: sessionId,
                timestamp: gap.timestamp.toISOString(),
                duration: gap.duration,
                session_time: gap.sessionTime,
              }),
            });
            console.log("✅ Gap saved to MongoDB");
          } catch (err) {
            console.warn("⚠️ Could not save gap to MongoDB:", err);
          }
        }
      }
      distractionStartTime.current = null;
    }
  }, [sessionId]);

  const handleGapClick = useCallback((gap: Gap) => {
    setSelectedGap(gap);
    setIsRecoveryOpen(true);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-950 via-zinc-900 to-zinc-950">
      {/* Ambient background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-violet-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 max-w-6xl mx-auto px-6 py-8">
        {/* Header */}
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-violet-400 via-cyan-400 to-violet-400 bg-clip-text text-transparent mb-2">
            Hindsight
          </h1>
          <p className="text-zinc-400">AI-Powered Context Recovery for Live Classes</p>
        </header>

        {/* Main Grid */}
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Video Player - Takes 2 columns */}
          <div className="lg:col-span-2 relative">
            <Classroom
              onTimeUpdate={setCurrentSessionTime}
              roomName={classroomRoom}
              onSessionCreated={handleSessionCreated}
            />
            <AttentionTracker
              onDistractionStart={handleDistractionStart}
              onDistractionEnd={handleDistractionEnd}
              currentSessionTime={currentSessionTime}
            />
          </div>

          {/* Timeline Sidebar */}
          <div className="lg:col-span-1">
            <div className="sticky top-8 p-4 rounded-2xl bg-zinc-900/50 border border-zinc-800 backdrop-blur-sm">
              <Timeline gaps={gaps} onGapClick={handleGapClick} sessionTime={currentSessionTime} />

              {/* Room info */}
              <div className="mt-4 pt-4 border-t border-zinc-800">
                <div className="text-xs text-zinc-500">
                  <span className="font-medium">Room:</span> {classroomRoom}
                </div>
                <div className="text-xs text-zinc-500 mt-1">
                  <span className="font-medium">Session:</span> {Math.floor(currentSessionTime / 60)}m {Math.floor(currentSessionTime % 60)}s
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recovery Modal */}
      <RecoveryMode
        isOpen={isRecoveryOpen}
        onClose={() => setIsRecoveryOpen(false)}
        gap={selectedGap}
        roomName={classroomRoom}
      />
    </div>
  );
}
