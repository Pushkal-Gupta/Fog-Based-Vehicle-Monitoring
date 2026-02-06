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
