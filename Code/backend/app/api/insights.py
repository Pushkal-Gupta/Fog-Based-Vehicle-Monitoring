from http.client import HTTPException
from fastapi import APIRouter, status
from app.models.insights import AIInsightPayload
from app.repositories.insights_repo import InsightRepo

router = APIRouter(prefix="/insights", tags=["insights"])

repo = InsightRepo()

@router.post(
    "/post_insights",
    status_code=status.HTTP_201_CREATED
)
async def submit_ai_insights(payload: AIInsightPayload):
    await repo.insert_ai_insight(payload)
    return {
        "status": "ok",
        "message": "AI insight stored and raw data marked as processed"
    }


@router.get(
    "/latest_ai_insight/{vehicle_id}",
    status_code=status.HTTP_200_OK
)
async def get_latest_insight(vehicle_id: str):
    insight = await repo.get_latest_insight(vehicle_id)

    if not insight:
        raise HTTPException(
            status_code=404,
            detail="No insights found for this vehicle"
        )

    return insight