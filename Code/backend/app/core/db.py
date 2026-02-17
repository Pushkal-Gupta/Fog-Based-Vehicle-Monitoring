
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
from app.core.config import settings

uri = settings.MONGO_URI
client = AsyncIOMotorClient(uri, server_api=ServerApi('1'))
db = client[settings.MONGO_DB_NAME]
vehicle_edge_state = db["vehicle_edge_state"] # fog to cloud data sent before AI processing
vehicle_latest_state_collection = db["vehicle_latest_state"] # only store the last recorded state might be used later on.
vehicle_ai_insights = db["vehicle_ai_insights"] # ai to cloud after processing
actuation_events = db["actuation_events"]
users = db["users"]
vehicles = db["vehicles"]
ownership_collection = db["vehicle_ownership"]


async def ping_server():
    try:
        await client.admin.command('ping')
        print("You successfully connected to MongoDB!")
    except Exception as e:
        print(e)
      