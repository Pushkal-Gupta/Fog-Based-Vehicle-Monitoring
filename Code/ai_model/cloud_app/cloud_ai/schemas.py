from pydantic import BaseModel, Field


class CloudInput(BaseModel):
    vehicle_id: str = Field(..., description="Vehicle identifier")
    timestamp_ms: int = Field(..., description="Unix timestamp in milliseconds")

    thermal_brake_margin: float
    thermal_engine_margin: float
    thermal_stress_index: float = Field(..., ge=0.0, le=1.0)

    mechanical_vibration_anomaly_score: float = Field(..., ge=0.0, le=1.0)
    mechanical_dominant_fault_band_hz: float = Field(..., gt=0.0)
    mechanical_vibration_rms: float = Field(..., ge=0.0)

    electrical_charging_efficiency_score: float = Field(..., ge=0.0, le=1.0)
    electrical_battery_health_pct: float = Field(..., ge=0.0, le=100.0)

    engine_rul_pct: float = Field(..., ge=0.0, le=100.0)
    brake_rul_pct: float = Field(..., ge=0.0, le=100.0)
    battery_rul_pct: float = Field(..., ge=0.0, le=100.0)

    vehicle_health_score: float = Field(..., ge=0.0, le=1.0)


class Recommendation(BaseModel):
    recommendation_service_priority: str
    recommendation_suggested_action: str
    recommendation_safe_operating_limit_km: int
    recommendation_source: str = "rule_based"


class CloudOutput(BaseModel):
    vehicle_id: str
    timestamp_ms: int

    engine_rul_pct: float
    brake_rul_pct: float
    battery_rul_pct: float
    fault_failure_probability_7d: float

    fault_primary: str
    fault_contributing_factors: list[str]

    recommendation: Recommendation
    history_points_used: int = 0
