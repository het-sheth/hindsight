# MongoDB Atlas Setup Guide for Hindsight

This guide will help you set up MongoDB Atlas for the Hindsight project and claim your $50 student credit + M5GO IoT Starter Kit prize!

## 🎓 Step 1: Sign Up for MongoDB Atlas (Student Credit)

1. **Go to MongoDB Atlas Student Program:**
   - Visit: https://www.mongodb.com/students
   - Click "Get Started" or "Sign Up"

2. **Create Your Account:**
   - Use your **student email** (`.edu` or verified student email)
   - Verify your email address

3. **Claim $50 Student Credit:**
   - After sign-up, navigate to "Billing" in the Atlas dashboard
   - Apply your student credit code (if provided)
   - Alternatively, start with the **FREE Forever Tier** (no credit card required)

## 🚀 Step 2: Create Your First Cluster

1. **Start a New Project:**
   - Click "New Project" in Atlas dashboard
   - Name it: `hindsight` or `hindsight-hackathon`
   - Click "Create Project"

2. **Build a Database Cluster:**
   - Click "Build a Database"
   - Choose **M0 FREE** tier (perfect for development, 512 MB storage)
   - Select a cloud provider: **AWS**, **Google Cloud**, or **Azure**
   - Choose a region closest to you (for best performance)
   - Cluster Name: `hindsight-cluster`
   - Click "Create"

## 🔐 Step 3: Configure Database Access

1. **Create Database User:**
   - Go to "Database Access" in left sidebar
   - Click "Add New Database User"
   - Authentication Method: **Password**
   - Username: `hindsight_admin` (or your choice)
   - Password: **Generate a secure password** (save it!)
   - Database User Privileges: **Read and write to any database**
   - Click "Add User"

2. **Configure Network Access:**
   - Go to "Network Access" in left sidebar
   - Click "Add IP Address"
   - For **development**: Click "Allow Access from Anywhere" (0.0.0.0/0)
   - For **production**: Add your specific IP address
   - Click "Confirm"

## 🔗 Step 4: Get Your Connection String

1. **Navigate to Database:**
   - Click "Database" in left sidebar
   - Find your cluster (`hindsight-cluster`)
   - Click "Connect" button

2. **Choose Connection Method:**
   - Select "Drivers"
   - Driver: **Python** (for backend) or **Node.js** (works for both)
   - Version: Latest

3. **Copy Connection String:**
   - You'll see something like:
     ```
     mongodb+srv://<username>:<password>@hindsight-cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority
     ```
   - **Copy this entire string**

## ⚙️ Step 5: Configure Hindsight

1. **Update `.env.local` file:**
   - Open: `c:\Users\hetsh\Desktop\hindsight\.env.local`
   - Find the MongoDB section:
     ```bash
     # MongoDB Atlas
     MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
     MONGODB_DB_NAME=hindsight
     ```

2. **Replace with your connection string:**
   ```bash
   # MongoDB Atlas
   MONGODB_URI=mongodb+srv://hindsight_admin:YOUR_PASSWORD@hindsight-cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority
   MONGODB_DB_NAME=hindsight
   ```

   **IMPORTANT:** Replace:
   - `<username>` → Your database username (e.g., `hindsight_admin`)
   - `<password>` → Your database password
   - `<cluster>` → Your cluster name (e.g., `hindsight-cluster.xxxxx`)

## 📦 Step 6: Install Dependencies

```bash
cd c:\Users\hetsh\Desktop\hindsight
pip install -r requirements.txt
```

This will install:
- `motor>=3.3.0` - Async MongoDB driver
- `pymongo>=4.6.0` - MongoDB sync driver
- `dnspython>=2.4.0` - Required for Atlas connection

## ▶️ Step 7: Start the Backend

```bash
cd backend
python main.py
```

You should see:
```
✅ Connected to MongoDB Atlas - Database: hindsight
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

## ✅ Step 8: Verify MongoDB Connection

### Check Database in Atlas Dashboard:
1. Go to "Database" → "Browse Collections"
2. You should see database: `hindsight`
3. Collections will be created automatically:
   - `sessions` - Classroom sessions
   - `gaps` - Attention gaps

### Test API Endpoints:

**Test 1: Create a Session**
```bash
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"room_name": "test-room", "student_identity": "test-student"}'
```

**Test 2: Get All Sessions**
```bash
curl http://localhost:8000/sessions
```

**Test 3: Create a Gap**
```bash
curl -X POST http://localhost:8000/gaps \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "YOUR_SESSION_ID_FROM_TEST_1",
    "timestamp": "2026-01-17T12:00:00Z",
    "duration": 5.5,
    "session_time": 120.0
  }'
```

## 🎯 Step 9: Run Full Application

### Terminal 1 - Backend:
```bash
cd backend
python main.py
```

### Terminal 2 - Agent:
```bash
cd agent
python main.py
```

### Terminal 3 - Frontend:
```bash
cd frontend
npm run dev
```

### Test the Full Flow:
1. Open http://localhost:3000
2. Allow webcam access
3. Look away from screen for 3+ seconds
4. Check browser console for: `✅ Gap saved to MongoDB`
5. Verify in MongoDB Atlas dashboard → Browse Collections → `gaps`

## 📊 MongoDB Features You're Using

### Collections Schema:

**`sessions` Collection:**
```json
{
  "_id": "ObjectId",
  "room_name": "hindsight-classroom",
  "student_identity": "student-user",
  "started_at": "2026-01-17T10:30:00Z",
  "ended_at": null,
  "total_duration": null,
  "total_gaps": 3
}
```

**`gaps` Collection:**
```json
{
  "_id": "ObjectId",
  "session_id": "6789abcd...",
  "timestamp": "2026-01-17T10:35:00Z",
  "duration": 4.5,
  "session_time": 300.0,
  "created_at": "2026-01-17T10:35:05Z"
}
```

### Indexes (Auto-created):
- `sessions`: `room_name`, `started_at`
- `gaps`: `session_id`, `timestamp`

## 🎁 Claiming the M5GO IoT Starter Kit Prize

To qualify for the **Best Use of MongoDB Atlas** prize:

### What You Built:
✅ **MongoDB Atlas Integration** - Real-time session and gap persistence
✅ **Async Driver (Motor)** - High-performance async operations
✅ **RESTful API** - FastAPI endpoints for CRUD operations
✅ **Aggregation Ready** - Analytics queries for student engagement
✅ **Atlas Free Tier** - No credit card required, perfect for students

### Hackathon Submission Checklist:
- [ ] MongoDB Atlas cluster deployed
- [ ] Database name: `hindsight`
- [ ] Collections: `sessions` and `gaps` populated with data
- [ ] Screenshots of MongoDB Atlas dashboard showing data
- [ ] README explaining MongoDB use case (see below)

### MongoDB Use Case for Judging:

**Problem:** Students lose focus during online classes and miss critical context.

**MongoDB Solution:**
1. **Session Tracking** - Stores classroom session metadata (start time, duration, room)
2. **Gap Analytics** - Logs attention lapses with precise timestamps
3. **Scalability** - Atlas handles multiple concurrent classrooms
4. **Real-time Queries** - Fast lookups for context recovery
5. **Future Analytics** - Aggregation pipeline for engagement insights

**Why MongoDB Atlas:**
- **Document Model** - Perfect for flexible session/gap schemas
- **Cloud-Native** - Serverless architecture, auto-scaling
- **Global Distribution** - Low-latency access for remote students
- **Atlas Search** - Future: semantic search through conversation transcripts

## 🔧 Troubleshooting

### Connection Error: "Authentication failed"
- Check username/password in connection string
- Verify user has "Read and write to any database" privileges

### Connection Error: "No DNS record found"
- Install `dnspython`: `pip install dnspython`
- Check cluster name is correct

### Connection Error: "IP not whitelisted"
- Go to "Network Access" in Atlas
- Add your IP or allow 0.0.0.0/0 for development

### "Database not available" in logs
- Check `.env.local` has correct `MONGODB_URI`
- Ensure backend loaded `.env.local` (check startup logs)
- MongoDB is optional - app works without it, just no persistence

## 📚 MongoDB University (Free Resources)

Get a head start with free courses:
- **M001: MongoDB Basics** - https://university.mongodb.com/courses/M001
- **M121: The MongoDB Aggregation Framework** - For analytics
- **M220P: MongoDB for Python Developers** - FastAPI integration

## 🎊 You're All Set!

Your Hindsight application now:
- ✅ Persists all classroom sessions to MongoDB Atlas
- ✅ Stores attention gaps for analytics
- ✅ Displays teacher video in classroom
- ✅ Qualifies for M5GO IoT Starter Kit prize
- ✅ Uses $50 student credit (or free tier)

**Next Steps:**
1. Test the application end-to-end
2. Screenshot MongoDB Atlas dashboard with data
3. Submit to hackathon with MongoDB Atlas integration highlighted
4. Win the M5GO IoT Starter Kit! 🏆

Good luck! 🚀
