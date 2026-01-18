# Hindsight API Reference

Backend API for LiveKit token generation and MongoDB persistence.

**Base URL:** `http://localhost:8000`

---

## 🎫 Authentication & Tokens

### `GET /token`
Generate LiveKit access token for joining a room.

**Query Parameters:**
- `room_name` (string, required) - Name of the LiveKit room to join

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "url": "wss://hindsight-mrp4jx96.livekit.cloud"
}
```

**Example:**
```bash
curl "http://localhost:8000/token?room_name=hindsight-classroom"
```

---

## 📚 Sessions (Classroom Sessions)

### `POST /sessions`
Create a new classroom session.

**Request Body:**
```json
{
  "room_name": "hindsight-classroom",
  "student_identity": "student-user"
}
```

**Response:**
```json
{
  "id": "6789abcd1234567890abcdef",
  "room_name": "hindsight-classroom",
  "student_identity": "student-user",
  "started_at": "2026-01-17T10:30:00Z",
  "ended_at": null,
  "total_duration": null,
  "total_gaps": 0
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"room_name": "hindsight-classroom", "student_identity": "student-user"}'
```

---

### `GET /sessions/{session_id}`
Get details of a specific session.

**Path Parameters:**
- `session_id` (string, required) - MongoDB ObjectId of the session

**Response:**
```json
{
  "id": "6789abcd1234567890abcdef",
  "room_name": "hindsight-classroom",
  "student_identity": "student-user",
  "started_at": "2026-01-17T10:30:00Z",
  "ended_at": "2026-01-17T11:15:00Z",
  "total_duration": 2700.0,
  "total_gaps": 3
}
```

**Example:**
```bash
curl http://localhost:8000/sessions/6789abcd1234567890abcdef
```

---

### `GET /sessions`
Get all sessions (paginated).

**Query Parameters:**
- `limit` (int, optional, default: 50) - Number of sessions to return
- `skip` (int, optional, default: 0) - Number of sessions to skip (pagination)

**Response:**
```json
[
  {
    "id": "6789abcd1234567890abcdef",
    "room_name": "hindsight-classroom",
    "student_identity": "student-user",
    "started_at": "2026-01-17T10:30:00Z",
    "ended_at": "2026-01-17T11:15:00Z",
    "total_duration": 2700.0,
    "total_gaps": 3
  },
  ...
]
```

**Example:**
```bash
# Get first 10 sessions
curl "http://localhost:8000/sessions?limit=10&skip=0"

# Get next 10 sessions
curl "http://localhost:8000/sessions?limit=10&skip=10"
```

---

### `PATCH /sessions/{session_id}/end`
Mark a session as ended.

**Path Parameters:**
- `session_id` (string, required) - MongoDB ObjectId of the session

**Query Parameters:**
- `total_duration` (float, required) - Total duration of the session in seconds

**Response:**
```json
{
  "message": "Session ended successfully"
}
```

**Example:**
```bash
curl -X PATCH "http://localhost:8000/sessions/6789abcd1234567890abcdef/end?total_duration=2700.0"
```

---

## ⏱️ Gaps (Attention Gaps)

### `POST /gaps`
Create a new attention gap.

**Request Body:**
```json
{
  "session_id": "6789abcd1234567890abcdef",
  "timestamp": "2026-01-17T10:35:00Z",
  "duration": 5.5,
  "session_time": 300.0
}
```

**Fields:**
- `session_id` (string) - MongoDB ObjectId of the parent session
- `timestamp` (ISO 8601 datetime) - When the distraction occurred
- `duration` (float) - How long the student was distracted (seconds)
- `session_time` (float) - Elapsed session time when gap started (seconds)

**Response:**
```json
{
  "id": "6789def012345678abcdef90",
  "session_id": "6789abcd1234567890abcdef",
  "timestamp": "2026-01-17T10:35:00Z",
  "duration": 5.5,
  "session_time": 300.0,
  "created_at": "2026-01-17T10:35:05Z"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/gaps \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "6789abcd1234567890abcdef",
    "timestamp": "2026-01-17T10:35:00Z",
    "duration": 5.5,
    "session_time": 300.0
  }'
```

**Note:** Creating a gap automatically increments the session's `total_gaps` counter.

---

### `GET /gaps/session/{session_id}`
Get all gaps for a specific session.

**Path Parameters:**
- `session_id` (string, required) - MongoDB ObjectId of the session

**Response:**
```json
[
  {
    "id": "6789def012345678abcdef90",
    "session_id": "6789abcd1234567890abcdef",
    "timestamp": "2026-01-17T10:35:00Z",
    "duration": 5.5,
    "session_time": 300.0,
    "created_at": "2026-01-17T10:35:05Z"
  },
  ...
]
```

**Example:**
```bash
curl http://localhost:8000/gaps/session/6789abcd1234567890abcdef
```

---

### `GET /gaps`
Get all gaps (paginated).

**Query Parameters:**
- `limit` (int, optional, default: 100) - Number of gaps to return
- `skip` (int, optional, default: 0) - Number of gaps to skip (pagination)

**Response:**
```json
[
  {
    "id": "6789def012345678abcdef90",
    "session_id": "6789abcd1234567890abcdef",
    "timestamp": "2026-01-17T10:35:00Z",
    "duration": 5.5,
    "session_time": 300.0,
    "created_at": "2026-01-17T10:35:05Z"
  },
  ...
]
```

**Example:**
```bash
# Get first 50 gaps
curl "http://localhost:8000/gaps?limit=50&skip=0"
```

---

## 🏥 Health Check

### `GET /`
Check if API is running.

**Response:**
```json
{
  "message": "Hindsight API",
  "status": "running"
}
```

**Example:**
```bash
curl http://localhost:8000/
```

---

## 🔧 Error Responses

All endpoints may return these error codes:

### `400 Bad Request`
Invalid request parameters or body.
```json
{
  "detail": "Invalid request format"
}
```

### `404 Not Found`
Resource not found.
```json
{
  "detail": "Session not found"
}
```

### `500 Internal Server Error`
Server error (e.g., database connection failed).
```json
{
  "detail": "Failed to create session: connection timeout"
}
```

### `503 Service Unavailable`
Database not available (MongoDB not configured).
```json
{
  "detail": "Database not available"
}
```

---

## 📊 Usage Analytics Queries

### Get Total Gaps Across All Sessions
```bash
curl http://localhost:8000/gaps | jq 'length'
```

### Get Average Gap Duration
```bash
curl http://localhost:8000/gaps | jq '[.[].duration] | add / length'
```

### Get Session with Most Gaps
```bash
curl http://localhost:8000/sessions | jq 'sort_by(.total_gaps) | reverse | .[0]'
```

### Get Gaps in Last Hour
```bash
curl http://localhost:8000/gaps | jq --arg since "$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ)" '[.[] | select(.timestamp > $since)]'
```

---

## 🐍 Python Client Example

```python
import requests
from datetime import datetime

BASE_URL = "http://localhost:8000"

# Create a session
response = requests.post(f"{BASE_URL}/sessions", json={
    "room_name": "hindsight-classroom",
    "student_identity": "student-user"
})
session = response.json()
session_id = session["id"]
print(f"Session created: {session_id}")

# Create a gap
response = requests.post(f"{BASE_URL}/gaps", json={
    "session_id": session_id,
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "duration": 5.5,
    "session_time": 300.0
})
gap = response.json()
print(f"Gap created: {gap['id']}")

# Get all gaps for session
response = requests.get(f"{BASE_URL}/gaps/session/{session_id}")
gaps = response.json()
print(f"Total gaps: {len(gaps)}")

# End session
response = requests.patch(f"{BASE_URL}/sessions/{session_id}/end?total_duration=2700.0")
print(response.json()["message"])
```

---

## 🌐 JavaScript/TypeScript Client Example

```typescript
const BASE_URL = "http://localhost:8000";

// Create a session
const createSession = async (roomName: string) => {
  const response = await fetch(`${BASE_URL}/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      room_name: roomName,
      student_identity: "student-user",
    }),
  });
  const session = await response.json();
  console.log("Session created:", session.id);
  return session.id;
};

// Create a gap
const createGap = async (sessionId: string, duration: number, sessionTime: number) => {
  const response = await fetch(`${BASE_URL}/gaps`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      timestamp: new Date().toISOString(),
      duration: duration,
      session_time: sessionTime,
    }),
  });
  const gap = await response.json();
  console.log("Gap created:", gap.id);
  return gap;
};

// Usage
const sessionId = await createSession("hindsight-classroom");
await createGap(sessionId, 5.5, 300.0);
```

---

## 📝 Notes

- **MongoDB Optional:** API works without MongoDB configured (returns 503 for database endpoints)
- **Auto-Indexing:** Database indexes are created automatically on startup
- **CORS Enabled:** Frontend at `http://localhost:3000` is whitelisted
- **UTC Timestamps:** All timestamps are in UTC format
- **ObjectId Format:** MongoDB ObjectIds are 24-character hex strings

---

## 🔗 Related Documentation

- [MONGODB_SETUP.md](./MONGODB_SETUP.md) - MongoDB Atlas setup guide
- [README.md](./README.md) - Full project documentation
- [LiveKit Docs](https://docs.livekit.io) - LiveKit integration
- [FastAPI Docs](https://fastapi.tiangolo.com) - API framework
