import time
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException
from app.core.db import vehicle_ai_insights, vehicle_edge_state
from app.models.insights import AIInsightPayload


class InsightRepo:

    async def insert_ai_insight(self, payload: AIInsightPayload):

        # 1️⃣ Validate ObjectId format
        try:
            source_object_id = ObjectId(payload.source_id)
        except (InvalidId, TypeError):
            raise HTTPException(
                status_code=400,
                detail="Invalid source_id format"
            )

        # 2️⃣ Check if source exists in vehicle_edge_state
        existing_source = await vehicle_edge_state.find_one(
            {"_id": source_object_id}
        )

        if not existing_source:
            raise HTTPException(
                status_code=404,
                detail="source_id not found in vehicle_edge_state"
            )

        # 3️⃣ Prepare AI insight document
        now_ts = int(time.time() * 1000)

        insight_doc = {
            **payload.model_dump(exclude={"source_id"}),
            "source_ref": source_object_id,   # Optional: keep reference
            "created_at": now_ts
        }

        # 4️⃣ Insert AI insight
        await vehicle_ai_insights.insert_one(insight_doc)

        # 5️⃣ Mark raw data as processed
        update_result = await vehicle_edge_state.update_one(
            {"_id": source_object_id},
            {
                "$set": {
                    "processing_meta.ai_processed": True,
                    "processing_meta.processed_at": now_ts,
                    "processing_meta.ai_version": "v1.0"
                }
            }
        )

        if update_result.matched_count == 0:
            raise HTTPException(
                status_code=500,
                detail="Failed to update vehicle_edge_state"
            )


    async def get_latest_insight(self, vehicle_id: str):
        document = await (
            vehicle_ai_insights
            .find({"vehicle_id": vehicle_id})
            .sort("timestamp_ms", -1)
            .limit(1)
            .to_list(length=1)
        )

        if not document:
            return None

        doc = document[0]
        doc["_id"] = str(doc["_id"])
        return doc