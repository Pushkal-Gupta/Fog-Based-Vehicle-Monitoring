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

    fog_actuation_limit_vehicle_speed_kph: int
    fog_actuation_disable_aggressive_braking: bool
    fog_actuation_enable_brake_cooling_fan: bool

    fog_decision_confidence: float
