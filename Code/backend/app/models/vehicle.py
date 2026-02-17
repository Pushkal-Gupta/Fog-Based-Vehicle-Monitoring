from pydantic import BaseModel, Field
from typing import Optional


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
    activation_code: str = Field(..., min_length=4, max_length=10)


class ClaimVehicleResponse(BaseModel):
    status: str
    vehicle_id: str
