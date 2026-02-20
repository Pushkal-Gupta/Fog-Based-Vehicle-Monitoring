from fastapi import status, APIRouter, Query, HTTPException
from typing import Optional
from app.repositories.intelligence_repo import IntelligenceRepo
from app.models.intelligence import IntelligencePayload 
router = APIRouter(prefix="/intelligence", tags=["intelligence"])
repo = IntelligenceRepo()



@router.get("/data/unprocessed")
async def get_unprocessed_vehicle_data(
    vehicle_id: Optional[str] = Query(None, description="Filter by vehicle ID"),
    limit: int = Query(10, description="Number of records to retrieve"),
):
    try:
        return await repo.get_unprocessed_vehicle_data(
            vehicle_id=vehicle_id,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch unprocessed vehicle data: {str(e)}"
        )


@router.get("/data/all")
async def get_all_vehicle_data(
    vehicle_id: Optional[str] = Query(None, description="Filter by vehicle ID"),
    limit: int = Query(10, description="Number of records to retrieve"),
):
    try:
        return await repo.get_all_vehicle_data(
            vehicle_id=vehicle_id,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch vehicle data: {str(e)}"
        )

@router.post("/insert", status_code=status.HTTP_201_CREATED)
async def ingest_vehicle_data(payload: IntelligencePayload):
    try:
        inserted_id = await repo.insert_vehicle_data(payload)
        return {"inserted_id": str(inserted_id)}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to store vehicle data")
    