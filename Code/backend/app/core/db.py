import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
from app.core.config import settings

uri = settings.MONGO_URI
client = AsyncIOMotorClient(uri, server_api=ServerApi('1'))
db = client[settings.MONGO_DB_NAME]
vehicle_intelligence_collection = db["vehicle_intelligence"]
vehicle_latest_state_collection = db["vehicle_latest_state"]
async def ping_server():
    try:
        await client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)
      