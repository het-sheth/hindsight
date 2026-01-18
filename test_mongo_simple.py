"""
Simple MongoDB Connection Test (Windows-friendly)
"""

import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import asyncio
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent / ".env.local"
load_dotenv(env_path)

async def test_connection():
    """Test MongoDB Atlas connection"""

    mongodb_uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB_NAME", "hindsight")

    print("=" * 60)
    print("MongoDB Atlas Connection Test")
    print("=" * 60)

    # Check if URI is configured
    if not mongodb_uri or mongodb_uri.startswith("mongodb+srv://<username>"):
        print("\nERROR: MongoDB URI not configured!")
        print("\nTo fix this:")
        print("1. Sign up at https://www.mongodb.com/cloud/atlas/register")
        print("2. Create a FREE M0 cluster")
        print("3. Get your connection string")
        print("4. Update MONGODB_URI in .env.local")
        return

    print(f"\nDatabase: {db_name}")
    print(f"Connecting to MongoDB Atlas...")

    try:
        # Create client
        client = AsyncIOMotorClient(mongodb_uri)

        # Test connection
        await client.admin.command('ping')
        print("\nSUCCESS: Connected to MongoDB Atlas!")

        # Get database info
        db = client[db_name]
        collections = await db.list_collection_names()

        print(f"\nCollections in '{db_name}':")
        if collections:
            for col in collections:
                count = await db[col].count_documents({})
                print(f"   - {col}: {count} documents")
        else:
            print("   (No collections yet - will be created automatically)")

        print("\nMongoDB Atlas is ready!")
        print("\nNext steps:")
        print("   1. Start backend: cd backend && python main.py")
        print("   2. Start agent: cd agent && python main.py")
        print("   3. Start frontend: cd frontend && npm run dev")
        print("   4. Open http://localhost:3000")

        client.close()

    except Exception as e:
        print(f"\nERROR: Connection failed!")
        print(f"Details: {str(e)}")
        print("\nTroubleshooting:")
        print("   - Check username and password in connection string")
        print("   - Verify IP is whitelisted (Network Access in Atlas)")
        print("   - Ensure database user has correct permissions")
        print("   - If password has special characters, they must be URL-encoded")
        print("     = becomes %3D, ; becomes %3B, @ becomes %40")

if __name__ == "__main__":
    asyncio.run(test_connection())
