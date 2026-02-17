from pydantic import BaseModel


class ActuationEventPayload(BaseModel):
    timestamp_ms: int
    decision_origin: str
    cloud_dependency: bool

    trigger_measured_brake_temp_c: float
    trigger_brake_temp_rise_rate: float
    trigger_brake_health_index: float

    fog_decision_critical_class: int
    fog_decision_actuation_triggered: int
    fog_decision_confidence: float

    fog_thermal_protection_active: bool
    fog_brake_stress_mitigation_active: bool
    fog_vibration_damping_mode_active: bool
    fog_predictive_service_required: bool
    fog_emergency_safeguard_active: bool
