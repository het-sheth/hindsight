# 🚀 Hindsight - Quick Start Guide

Get Hindsight running with MongoDB Atlas in 10 minutes!

---

## ⚡ Prerequisites

- **Python 3.8+** installed
- **Node.js 18+** and npm installed
- **Git** (optional, for cloning)
- **MongoDB Atlas account** (free, no credit card needed)

---

## 📋 Step 1: MongoDB Atlas Setup (5 minutes)

### 1.1 Create Free Account
1. Go to https://www.mongodb.com/cloud/atlas/register
2. Sign up with email or Google
3. Choose **FREE M0 cluster** (512 MB, perfect for development)
4. Select a region closest to you
5. Cluster name: `hindsight-cluster`
6. Click **Create**

### 1.2 Configure Access
1. **Create Database User:**
   - Username: `hindsight_admin`
   - Password: Generate secure password (save it!)
   - Role: Atlas Admin or Read/Write to any database

2. **Whitelist IP:**
   - Click "Network Access" → "Add IP Address"
   - Choose "Allow Access from Anywhere" (0.0.0.0/0)
   - Click "Confirm"

### 1.3 Get Connection String
1. Click "Connect" on your cluster
2. Choose "Connect your application"
3. Driver: **Python** (version 3.12+)
4. Copy the connection string:
   ```
   mongodb+srv://<username>:<password>@hindsight-cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
5. Replace `<username>` and `<password>` with your actual credentials

---

## 🔧 Step 2: Configure Environment (2 minutes)

### 2.1 Update `.env.local`
Open `c:\Users\hetsh\Desktop\hindsight\.env.local` and replace the MongoDB section:

```bash
# MongoDB Atlas
MONGODB_URI=mongodb+srv://hindsight_admin:YOUR_PASSWORD_HERE@hindsight-cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=hindsight
```

**IMPORTANT:** Replace:
- `YOUR_PASSWORD_HERE` with your database password
- `xxxxx` with your actual cluster ID

### 2.2 Verify Other API Keys
Make sure you have all required API keys in `.env.local`:
- ✅ `LIVEKIT_URL`
- ✅ `LIVEKIT_API_KEY`
- ✅ `LIVEKIT_API_SECRET`
- ✅ `DEEPGRAM_API_KEY`
- ✅ `ELEVENLABS_API_KEY`
- ✅ `OPENROUTER_API_KEY`
- ✅ `NEXT_PUBLIC_OVERSHOOT_API_KEY`
- ✅ `MONGODB_URI` (just added)

---

## 📦 Step 3: Install Dependencies (2 minutes)

### 3.1 Backend Dependencies
```bash
cd c:\Users\hetsh\Desktop\hindsight
pip install -r requirements.txt
```

Expected packages:
- FastAPI, Uvicorn
- LiveKit API & Agents
- Deepgram, ElevenLabs, OpenAI plugins
- **Motor, PyMongo, dnspython** (MongoDB)

### 3.2 Frontend Dependencies
```bash
cd frontend
npm install
```

---

## ▶️ Step 4: Start All Services (1 minute)

You need **3 terminal windows**:

### Terminal 1: Backend
```bash
cd c:\Users\hetsh\Desktop\hindsight\backend
python main.py
```

**Expected output:**
```
✅ Connected to MongoDB Atlas - Database: hindsight
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

If you see `⚠️ MongoDB URI not configured`, check your `.env.local` file.

### Terminal 2: Agent
```bash
cd c:\Users\hetsh\Desktop\hindsight\agent
python main.py
```

**Expected output:**
```
INFO:livekit.agents: Connecting to LiveKit...
INFO:livekit.agents: Worker started
```

### Terminal 3: Frontend
```bash
cd c:\Users\hetsh\Desktop\hindsight\frontend
npm run dev
```

**Expected output:**
```
  ▲ Next.js 15.1.3
  - Local:        http://localhost:3000
```

---

## ✅ Step 5: Test the Application (5 minutes)

### 5.1 Open Browser
Go to **http://localhost:3000**

### 5.2 Allow Webcam Access
Browser will prompt for camera permission - click **Allow**.

### 5.3 Verify Components

**You should see:**
- ✅ Main classroom area (top-left badge: "🎓 In Classroom")
- ✅ Small webcam preview (bottom-right corner)
- ✅ Attention status: "👀 Focused" (green, top-right)
- ✅ "Missed Context" sidebar (right side, empty initially)
- ✅ Session timer counting up

**Browser Console (F12):**
```
✅ Session created: 6789abcd1234567890abcdef
Overshoot Raw Result: {...}
```

### 5.4 Test Attention Tracking

**Test 1: Look Away**
1. Look away from your screen or cover webcam
2. Wait 2-3 seconds
3. Status should change to: **"⚠️ Look at screen!"** (red, pulsing)

**Test 2: Return Focus**
1. Look back at screen
2. Status returns to: **"👀 Focused"** (green)
3. A new gap appears in "Missed Context" sidebar

**Browser Console:**
```
✅ Gap saved to MongoDB
```

### 5.5 Test Context Recovery

1. Click on a gap in the "Missed Context" sidebar
2. Modal opens: **"🧠 Hindsight Recovery"**
3. Wait for connection to AI voice assistant
4. Speak: *"What did I miss?"*
5. Hindsight AI responds with explanation

### 5.6 Verify MongoDB Persistence

**Option A: MongoDB Atlas Dashboard**
1. Go to https://cloud.mongodb.com
2. Click "Browse Collections"
3. Database: `hindsight`
4. Collections:
   - **sessions** - Should have 1 document (your current session)
   - **gaps** - Should have documents for each distraction

**Option B: API Endpoints**
```bash
# Get all sessions
curl http://localhost:8000/sessions

# Get all gaps
curl http://localhost:8000/gaps
```

---

## 🎯 Success Criteria

You've successfully set up Hindsight if:

- [x] Backend shows "✅ Connected to MongoDB Atlas"
- [x] Frontend loads at http://localhost:3000
- [x] Webcam preview shows your face
- [x] Attention status changes when you look away
- [x] Gaps appear in sidebar after looking away
- [x] Browser console shows "✅ Gap saved to MongoDB"
- [x] MongoDB Atlas has documents in `sessions` and `gaps` collections
- [x] Clicking a gap opens recovery modal with AI voice assistant

---

## 🐛 Troubleshooting

### Backend won't connect to MongoDB
**Error:** `❌ Failed to connect to MongoDB: Authentication failed`

**Fix:**
1. Check `.env.local` has correct username/password
2. Verify user exists in Atlas → Database Access
3. Ensure user has "Read and write to any database" permission

---

### "IP not whitelisted" error
**Error:** `MongoServerError: IP address not allowed`

**Fix:**
1. Go to Atlas → Network Access
2. Click "Add IP Address"
3. Click "Allow Access from Anywhere" (0.0.0.0/0)
4. Click "Confirm"

---

### Overshoot not detecting attention
**Issue:** Status stuck on "🔄 Loading Overshoot..." or always "Focused"

**Fix:**
1. Check webcam preview shows your face clearly
2. Ensure good lighting (not too dark)
3. Press `d` key to toggle debug overlay - check raw Overshoot responses
4. Verify `NEXT_PUBLIC_OVERSHOOT_API_KEY` in `.env.local`

---

### Teacher video not showing
**Issue:** Only see waiting room, no teacher video

**Fix:**
1. Teacher must join the same room: `hindsight-classroom`
2. Teacher needs LiveKit token for the room
3. Verify `LIVEKIT_URL` and credentials are correct
4. Check LiveKit dashboard for active rooms

---

### Frontend API errors
**Error:** `Failed to fetch` or CORS errors in console

**Fix:**
1. Ensure backend is running on port 8000
2. Check `API_BASE_URL` in `page.tsx` is `http://localhost:8000`
3. Verify CORS middleware allows `http://localhost:3000`

---

## 🎁 Next Steps

### For Development:
- Read [API_REFERENCE.md](./API_REFERENCE.md) for endpoint documentation
- Check [MONGODB_SETUP.md](./MONGODB_SETUP.md) for advanced Atlas features
- Review [CHANGES_SUMMARY.md](./CHANGES_SUMMARY.md) for implementation details

### For Hackathon Submission:
- Screenshot MongoDB Atlas dashboard showing data
- Record demo video showing:
  - Attention tracking in action
  - Gaps being saved to MongoDB
  - AI context recovery conversation
- Highlight MongoDB use case in README
- Mention $50 student credit and M5GO IoT prize eligibility

### For Production:
- Restrict MongoDB Network Access to specific IPs (not 0.0.0.0/0)
- Use environment-specific `.env` files
- Enable MongoDB Atlas monitoring and alerts
- Add user authentication (session.student_identity from login)
- Implement MongoDB aggregation queries for analytics

---

## 📊 MongoDB Atlas Student Benefits

**What You Get:**
- ✅ $50 credit for MongoDB Atlas (students only)
- ✅ M0 Free Tier forever (no credit card required)
- ✅ 512 MB storage (perfect for this project)
- ✅ Access to MongoDB University courses (free)
- ✅ Chance to win M5GO IoT Starter Kit

**Apply for Credit:**
- https://www.mongodb.com/students
- Use your student email (.edu)

---

## 🏆 Ready to Win!

Your Hindsight project now:
- ✅ Uses MongoDB Atlas for persistence
- ✅ Displays teacher video in classroom
- ✅ Tracks attention gaps in real-time
- ✅ Provides AI-powered context recovery
- ✅ Qualifies for Best Use of MongoDB Atlas prize

**Happy hacking! 🚀**

Need help? Check:
- [Full Documentation](./README.md)
- [MongoDB Setup Guide](./MONGODB_SETUP.md)
- [API Reference](./API_REFERENCE.md)
- [MongoDB Atlas Docs](https://www.mongodb.com/docs/atlas/)
