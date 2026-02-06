from pydantic import BaseModel, Field
from typing import List, Optional




class ThermalInsights(BaseModel):
    brake_thermal_margin: float
    engine_thermal_margin: float


class MechanicalInsights(BaseModel):
    vibration_anomaly_score: float
    dominant_fault_band_hz: int


class ElectricalInsights(BaseModel):
    charging_efficiency_score: float
    battery_degradation_trend: str


class UsageBehaviorInsights(BaseModel):
    driver_aggression_score: float
    stress_amplification_factor: float


class HealthVectors(BaseModel):
    thermal: ThermalInsights
    mechanical: MechanicalInsights
    electrical: ElectricalInsights
    usage_behavior: UsageBehaviorInsights



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



class AIInsightPayload(BaseModel):
    source_id: str = Field(..., description="Mongo _id of raw edge document")
    vehicle_id: str
    timestamp_ms: int

    health_vectors: HealthVectors
    rul_estimates: RulEstimates
    fault_inference: FaultInference

    vehicle_health_score: float
    recommendations: Recommendations
