from fastapi import APIRouter, Query
from typing import List, Optional
from app.repositories.intelligence_repo import IntelligenceRepo
from fastapi import HTTPException, status
from app.models.ingest import IngestPayload
router = APIRouter()


repo = IntelligenceRepo()


@router.get("/data", response_model=List[IngestPayload])
async def get_vehicle_data(
    vehicle_id: Optional[str] = Query(None, description="Filter by vehicle ID"),
    limit: int = Query(10, description="Number of records to retrieve"),
):
    try:
        data = await repo.get_vehicle_data(vehicle_id=vehicle_id, limit=limit)
        return data
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch vehicle data")