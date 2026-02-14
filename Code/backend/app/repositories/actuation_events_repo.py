import time
from app.core.db import actuation_events
from app.models.actuation_event import ActuationEventPayload


class ActuationRepo:

    async def insert_actuation_event(self, payload: ActuationEventPayload):
        document = {
            **payload.model_dump(),
            "ingested_at": int(time.time() * 1000)
        }

        result = await actuation_events.insert_one(document)
        return str(result.inserted_id)

    async def get_latest_actuation_event(self):
        document = await (
            actuation_events
            .find({})
            .sort("timestamp_ms", -1)
            .limit(1)
            .to_list(length=1)
        )

        if not document:
            return None

        doc = document[0]
        doc["_id"] = str(doc["_id"])
        return doc

    async def get_actuation_history(self, limit: int = 10):
        cursor = (
            actuation_events
            .find({})
            .sort("timestamp_ms", -1)
            .limit(limit)
        )

        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)

        return results
