from pydantic import BaseModel
from typing import List, Optional




class ThermalHealth(BaseModel):
    brake_thermal_margin: float
    engine_thermal_margin: float


class MechanicalHealth(BaseModel):
    vibration_anomaly_score: float
    dominant_fault_band_hz: int


class ElectricalHealth(BaseModel):
    charging_efficiency_score: float
    battery_degradation_trend: str


class UsageBehavior(BaseModel):
    driver_aggression_score: float
    stress_amplification_factor: float


class HealthVectors(BaseModel):
    thermal: ThermalHealth
    mechanical: MechanicalHealth
    electrical: ElectricalHealth
    usage_behavior: UsageBehavior



class RulEstimates(BaseModel):
    engine_rul_pct: int
    brake_rul_pct: int
    battery_rul_pct: int


class FaultInference(BaseModel):
    primary_fault: str
    contributing_factors: List[str]
    failure_probability_7d: float


class Recommendations(BaseModel):
    service_priority: str
    suggested_action: str
    safe_operating_limit_km: int




class IngestPayload(BaseModel):
    vehicle_id: str
    timestamp_ms: int
    health_vectors: HealthVectors
    rul_estimates: Optional[RulEstimates] = None
    fault_inference: Optional[FaultInference] = None
    vehicle_health_score: Optional[float] = None
    recommendations: Optional[Recommendations] = None
