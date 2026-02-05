from app.core.db import vehicle_intelligence_collection
from app.models.ingest import IngestPayload
from typing import List, Optional


class IntelligenceRepo:
    async def insert_vehicle_data(self, payload: IngestPayload):
        result = await vehicle_intelligence_collection.insert_one(payload.dict())
        return result.inserted_id

    async def get_vehicle_data(self, vehicle_id: Optional[str] = None, limit: int = 10) -> List[IngestPayload]:
        query = {}
        if vehicle_id:
            query["vehicle_id"] = vehicle_id
        cursor = vehicle_intelligence_collection.find(query).sort("timestamp_ms", -1).limit(limit)
        results = []
        async for doc in cursor:
            results.append(IngestPayload(**doc))
        return results

    