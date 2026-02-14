from pydantic import BaseModel


class IntelligencePayload(BaseModel):
    vehicle_id: str
    timestamp_ms: int

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
