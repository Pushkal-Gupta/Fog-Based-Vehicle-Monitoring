from app.core.db import vehicle_edge_state
from app.models.intelligence import IntelligencePayload
from typing import Optional
import time
import math






class IntelligenceRepo:

    # -------------------------------
    # FLOAT VALIDATION HELPER
    # -------------------------------
    def _validate_no_invalid_floats(self, obj, path="root"):
        if isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj):
                raise ValueError(f"Invalid float at {path}: {obj}")

        elif isinstance(obj, dict):
            for k, v in obj.items():
                self._validate_no_invalid_floats(v, f"{path}.{k}")

        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                self._validate_no_invalid_floats(v, f"{path}[{i}]")

    # -------------------------------
    # FETCH WITH DEBUGGING
    # -------------------------------
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

            # 🔍 DEBUG VALIDATION
            try:
                self._validate_no_invalid_floats(doc)
            except ValueError as e:
                print("\n🚨 INVALID DOCUMENT DETECTED")
                print("Mongo _id:", doc["_id"])
                print("Vehicle ID:", doc.get("vehicle_id"))
                print("Timestamp:", doc.get("timestamp_ms"))
                print("Error:", str(e))
                print("Full document:", doc)
                raise  # crash so you see it immediately

            results.append(doc)

        return results

    # -------------------------------
    # PUBLIC METHODS
    # -------------------------------
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
        limit: int = 10
    ) -> list[dict]:

        query = {}

        if vehicle_id:
            query["vehicle_id"] = vehicle_id

        return await self._fetch(query, limit)


async def insert_vehicle_data(self, payload: IntelligencePayload):
    # Convert Pydantic model to dict
    document = {
        **payload.model_dump(),
        "processing_meta": {
            "ai_processed": False,
            "processed_at": None,
            "ai_version": None
        },
        "ingested_at": int(time.time() * 1000)
    }

    # 🔐 Sanitize all numeric values recursively
    def validate_numeric_values(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                obj[k] = validate_numeric_values(v)
        elif isinstance(obj, list):
            return [validate_numeric_values(item) for item in obj]
        elif isinstance(obj, float):
            if not math.isfinite(obj):
                raise ValueError("Non-finite numeric value detected (inf / -inf / NaN)")
        return obj

    validate_numeric_values(document)

    result = await vehicle_edge_state.insert_one(document)
    return str(result.inserted_id)