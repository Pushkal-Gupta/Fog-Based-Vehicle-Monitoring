from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class ActivationStatus(str, Enum):
    unclaimed = "unclaimed"
    claimed = "claimed"


class GenerateVehicleRequest(BaseModel):
    vehicle_id: str = Field(..., min_length=3, max_length=50)
    vin: Optional[str] = Field(None, min_length=11, max_length=17)
    dealership_name: str = Field(..., min_length=2, max_length=100)


class GenerateVehicleResponse(BaseModel):
    status: str
    vehicle_id: str
    activation_code: str


class ClaimVehicleRequest(BaseModel):
    vehicle_id: str = Field(..., min_length=3, max_length=50)
    activation_code: str = Field(..., min_length=6, max_length=6)


class ClaimVehicleResponse(BaseModel):
    status: str
    vehicle_id: str


class VehicleSummary(BaseModel):
    vehicle_id: str
    vin: Optional[str]
    dealership_name: str
    activation_status: ActivationStatus
    claimed_at: int


class MyVehiclesResponse(BaseModel):
    vehicles: List[VehicleSummary]


class VehicleDetailResponse(BaseModel):
    vehicle_id: str
    vin: Optional[str]
    dealership_name: str
    activation_status: ActivationStatus
    created_at: int
    claimed_at: int