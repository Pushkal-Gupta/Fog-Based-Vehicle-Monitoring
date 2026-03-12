"""Rule-based fault explanation engine (non-ML)."""

from cloud_ai.schemas import CloudInput


def explain_fault(data: CloudInput, failure_probability_7d: float) -> tuple[str, list[str]]:
    contributors: list[str] = []

    if data.thermal_stress_index > 0.75 and data.brake_rul_pct < 40:
        primary = "BRAKE_THERMAL_SATURATION"
    elif data.mechanical_vibration_anomaly_score > 0.7:
        primary = "MECHANICAL_VIBRATION_ANOMALY"
    elif data.electrical_charging_efficiency_score < 0.65 or data.electrical_battery_health_pct < 60:
        primary = "ELECTRICAL_DEGRADATION"
    elif failure_probability_7d > 0.65:
        primary = "MULTI_FACTOR_FAILURE_RISK"
    else:
        primary = "NO_DOMINANT_FAULT"

    if data.thermal_stress_index > 0.7:
        contributors.append("high_thermal_stress_index")

    if data.brake_rul_pct < 40:
        contributors.append("low_brake_rul_pct")

    if data.mechanical_vibration_anomaly_score > 0.65:
        contributors.append("high_mechanical_vibration_anomaly_score")

    if data.mechanical_vibration_rms > 0.8:
        contributors.append("high_mechanical_vibration_rms")

    if data.electrical_charging_efficiency_score < 0.7:
        contributors.append("low_electrical_charging_efficiency_score")

    if not contributors:
        contributors.append("no_dominant_contributor")

    return primary, contributors
