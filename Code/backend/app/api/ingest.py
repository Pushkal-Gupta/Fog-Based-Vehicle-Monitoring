from fastapi import APIRouter, Query
from typing import List, Optional
from app.repositories.intelligence_repo import IntelligenceRepo
from fastapi import HTTPException, status
from app.models.ingest import IngestPayload
router = APIRouter()


repo = IntelligenceRepo()


@router.post("/ingest", status_code=status.HTTP_201_CREATED)
async def ingest_vehicle_data(payload: IngestPayload):
    try:
        inserted_id = await repo.insert_vehicle_data(payload)
        return {"inserted_id": str(inserted_id)}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to store vehicle data")
    
