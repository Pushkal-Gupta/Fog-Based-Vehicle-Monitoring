from pydantic import BaseModel, Field


class AIInsightPayload(BaseModel):
    source_id: str = Field(...)

    vehicle_id: str
    timestamp_ms: int

    thermal_brake_margin: float
    thermal_engine_margin: float
    thermal_stress_index: float

    mechanical_vibration_anomaly_score: float
    mechanical_dominant_fault_band_hz: int
    mechanical_vibration_rms: float

    electrical_charging_efficiency_score: float
    electrical_battery_degradation_trend: str

    usage_driver_aggression_score: float
    usage_stress_amplification_factor: float

    engine_rul_pct: int
    brake_rul_pct: int
    battery_rul_pct: int

    fog_decision_critical_class: int
    fog_decision_actuation_triggered: int

    fault_primary: str
    fault_contributing_factor_1: str
    fault_contributing_factor_2: str
    fault_contributing_factor_3: str
    fault_failure_probability_7d: float

    vehicle_health_score: float

    recommendation_service_priority: str
    recommendation_suggested_action: str
    recommendation_safe_operating_limit_km: int
