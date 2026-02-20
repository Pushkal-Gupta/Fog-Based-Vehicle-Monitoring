from pydantic import BaseModel


class IntelligencePayload(BaseModel):
    vehicle_id: str
    timestamp_ms: int

    fog_decision_critical_class: int
    fog_decision_actuation_triggered: int
    fog_decision_confidence: float

    thermal_brake_margin: float
    thermal_engine_margin: float
    thermal_stress_index: float

    mechanical_vibration_anomaly_score: float
    mechanical_dominant_fault_band_hz: int
    mechanical_vibration_rms: float

    electrical_charging_efficiency_score: float
    electrical_battery_health_pct: int

    engine_rul_pct: int
    brake_rul_pct: int
    battery_rul_pct: int

    vehicle_health_score: float

    trigger_measured_brake_temp_c: float
    trigger_brake_temp_rise_rate: float
    trigger_brake_health_index: float

    fog_thermal_protection_active: bool
    fog_brake_stress_mitigation_active: bool
    fog_vibration_damping_mode_active: bool
    fog_predictive_service_required: bool
    fog_emergency_safeguard_active: bool