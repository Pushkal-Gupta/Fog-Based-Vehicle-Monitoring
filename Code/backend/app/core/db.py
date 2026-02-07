import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
from app.core.config import settings

uri = settings.MONGO_URI
client = AsyncIOMotorClient(uri, server_api=ServerApi('1'))
db = client[settings.MONGO_DB_NAME]
vehicle_edge_state = db["vehicle_edge_state"]
vehicle_latest_state_collection = db["vehicle_latest_state"]
vehicle_ai_insights = db["vehicle_ai_insights"]
async def ping_server():
    try:
        await client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)
      