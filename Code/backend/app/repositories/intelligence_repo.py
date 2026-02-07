from app.core.db import vehicle_edge_state
from app.models.ingest import IngestPayload
from typing import List, Optional
import time

class IntelligenceRepo:

    async def _fetch(
        self,
        query: dict,
        limit: int
    ) -> list[dict]:

        cursor = (
            vehicle_edge_state
            .find(query)
            .sort("timestamp_ms", -1)
            .limit(limit)
        )

        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)

        return results
    
    async def get_unprocessed_vehicle_data(
        self,
        vehicle_id: Optional[str] = None,
        limit: int = 10
    ) -> list[dict]:

        query = {
            "processing_meta.ai_processed": False
        }

        if vehicle_id:
            query["vehicle_id"] = vehicle_id

        return await self._fetch(query, limit)
    
    
    async def get_all_vehicle_data(
        self,
        vehicle_id: Optional[str] = None,
        limit: int = 10) -> list[dict]:

            query = {}
            if vehicle_id:
                query["vehicle_id"] = vehicle_id

            return await self._fetch(query, limit)

    