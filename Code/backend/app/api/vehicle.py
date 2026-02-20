import time
import random
import string
from fastapi import APIRouter, Depends, HTTPException
from app.utils.auth.admin import verify_admin
from app.utils.auth.auth import get_current_user
from app.utils.auth.user_service import ensure_user_exists
from app.core.db import vehicles as vehicles_collection, ownership_collection

from app.models.vehicle import *


router = APIRouter(prefix="/vehicle", tags=["vehicle"])


def generate_activation_code(length: int = 6):
    return ''.join(random.choices(string.digits, k=length))








@router.post("/generate_vehicle", response_model=GenerateVehicleResponse)
async def generate_vehicle(
    payload: GenerateVehicleRequest,
    _=Depends(verify_admin)
):

    existing = await vehicles_collection.find_one(
        {"vehicle_id": payload.vehicle_id}
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Vehicle already exists"
        )

    activation_code = generate_activation_code()

    await vehicles_collection.insert_one({
        "vehicle_id": payload.vehicle_id,
        "vin": payload.vin,
        "dealership_name": payload.dealership_name,
        "activation_code": activation_code,
        "activation_status": "unclaimed",
        "created_at": int(time.time() * 1000)
    })

    return GenerateVehicleResponse(
        status="vehicle created",
        vehicle_id=payload.vehicle_id,
        activation_code=activation_code
    )

@router.post("/claim", response_model=ClaimVehicleResponse)
async def claim_vehicle(
    payload: ClaimVehicleRequest,
    user=Depends(get_current_user)
):

    uid = await ensure_user_exists(user)

    vehicle = await vehicles_collection.find_one({
        "vehicle_id": payload.vehicle_id,
        "activation_code": payload.activation_code,
        "activation_status": "unclaimed"
    })

    if not vehicle:
        raise HTTPException(
            status_code=400,
            detail="Invalid vehicle ID or activation code"
        )

    # Mark vehicle as claimed
    await vehicles_collection.update_one(
        {"vehicle_id": payload.vehicle_id},
        {"$set": {"activation_status": "claimed"}}
    )

    # Create ownership mapping
    await ownership_collection.insert_one({
        "user_id": uid,
        "vehicle_id": payload.vehicle_id,
        "claimed_at": int(time.time() * 1000)
    })

    return ClaimVehicleResponse(
        status="vehicle successfully claimed",
        vehicle_id=payload.vehicle_id
    )


@router.get("/my", response_model=MyVehiclesResponse)
async def get_my_vehicles(
    user=Depends(get_current_user)
):

    uid = await ensure_user_exists(user)

    ownerships = ownership_collection.find({"user_id": uid})

    vehicles = []

    async for record in ownerships:
        vehicle = await vehicles_collection.find_one(
            {"vehicle_id": record["vehicle_id"]}
        )

        if vehicle:
            vehicles.append(
                VehicleSummary(
                    vehicle_id=vehicle["vehicle_id"],
                    vin=vehicle.get("vin"),
                    dealership_name=vehicle["dealership_name"],
                    activation_status=vehicle["activation_status"],
                    claimed_at=record["claimed_at"]
                )
            )

    return MyVehiclesResponse(vehicles=vehicles)


@router.get("/{vehicle_id}", response_model=VehicleDetailResponse)
async def get_vehicle_detail(
    vehicle_id: str,
    user=Depends(get_current_user)
):

    uid = await ensure_user_exists(user)

    ownership = await ownership_collection.find_one({
        "vehicle_id": vehicle_id,
        "user_id": uid
    })

    if not ownership:
        raise HTTPException(status_code=403, detail="Not authorized")

    vehicle = await vehicles_collection.find_one({
        "vehicle_id": vehicle_id
    })

    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    return VehicleDetailResponse(
        vehicle_id=vehicle["vehicle_id"],
        vin=vehicle.get("vin"),
        dealership_name=vehicle["dealership_name"],
        activation_status=vehicle["activation_status"],
        created_at=vehicle["created_at"],
        claimed_at=ownership["claimed_at"]
    )