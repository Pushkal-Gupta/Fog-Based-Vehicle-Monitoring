import time
from bson import ObjectId
from app.core.db import vehicle_ai_insights, vehicle_edge_state
from app.models.insights import AIInsightPayload


class InsightRepo:

    async def insert_ai_insight(self, payload: AIInsightPayload):

        insight_doc = {
            **payload.model_dump(exclude={"source_id"}),
            "created_at": int(time.time() * 1000)
        }

        await vehicle_ai_insights.insert_one(insight_doc)

        await vehicle_edge_state.update_one(
            {"_id": ObjectId(payload.source_id)},
            {
                "$set": {
                    "processing_meta.ai_processed": True,
                    "processing_meta.processed_at": int(time.time() * 1000),
                    "processing_meta.ai_version": "v1.0"
                }
            }
        )
