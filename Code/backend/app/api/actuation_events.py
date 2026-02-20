from fastapi import APIRouter, status, HTTPException, Query
from typing import Optional
from app.models.actuation_event import ActuationEventPayload
from app.repositories.actuation_events_repo import ActuationRepo

router = APIRouter(prefix="/actuation_events", tags=["actuation_events"])

repo = ActuationRepo()


@router.post(
    "/insert",
    status_code=status.HTTP_201_CREATED
)
async def submit_actuation_event(payload: ActuationEventPayload):
    await repo.insert_actuation_event(payload)
    return {
        "status": "ok",
        "message": "Actuation event stored"
    }


@router.get(
    "/latest",
    status_code=status.HTTP_200_OK
)
async def get_latest_actuation_event():
    event = await repo.get_latest_actuation_event()

    if not event:
        raise HTTPException(
            status_code=404,
            detail="No actuation events found"
        )

    return event


@router.get(
    "/history",
    status_code=status.HTTP_200_OK
)
async def get_actuation_history(
    limit: int = Query(10, description="Number of events to retrieve")
):
    return await repo.get_actuation_history(limit=limit)
