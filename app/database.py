import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "northstar_bot")

client = AsyncIOMotorClient(MONGODB_URI)
db = client[MONGODB_DB]

users_collection = db["users"]
conversations_collection = db["conversations"]
bookings_collection = db["bookings"]