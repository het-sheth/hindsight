"""
Quick MongoDB Connection Test
Run this to verify your Atlas connection works
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
    print("🔍 MongoDB Atlas Connection Test")
    print("=" * 60)

    # Check if URI is configured
    if not mongodb_uri or mongodb_uri == "mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority":
        print("\n❌ MongoDB URI not configured!")
        print("\n📝 To fix this:")
        print("1. Sign up at https://www.mongodb.com/cloud/atlas/register")
        print("2. Create a FREE M0 cluster (no credit card needed)")
        print("3. Get your connection string")
        print("4. Update MONGODB_URI in .env.local")
        print("\n📚 See MONGODB_SETUP.md for detailed instructions")
        return

    print(f"\n📊 Database: {db_name}")
    print(f"🔗 Connecting to MongoDB Atlas...")

    try:
        # Create client
        client = AsyncIOMotorClient(mongodb_uri)

        # Test connection
        await client.admin.command('ping')
        print("\n✅ Successfully connected to MongoDB Atlas!")

        # Get database info
        db = client[db_name]
        collections = await db.list_collection_names()

        print(f"\n📁 Collections in '{db_name}':")
        if collections:
            for col in collections:
                count = await db[col].count_documents({})
                print(f"   - {col}: {count} documents")
        else:
            print("   (No collections yet - they'll be created automatically)")

        print("\n🎉 MongoDB Atlas is ready to use!")
        print("\n💡 Next steps:")
        print("   1. Start the backend: cd backend && python main.py")
        print("   2. Start the agent: cd agent && python main.py")
        print("   3. Start the frontend: cd frontend && npm run dev")
        print("   4. Open http://localhost:3000 and test the app!")

        client.close()

    except Exception as e:
        print(f"\n❌ Connection failed: {str(e)}")
        print("\n🔧 Troubleshooting:")
        print("   - Check username and password in connection string")
        print("   - Verify IP is whitelisted (Network Access in Atlas)")
        print("   - Ensure database user has correct permissions")
        print("\n📚 See MONGODB_SETUP.md for help")

if __name__ == "__main__":
    asyncio.run(test_connection())
