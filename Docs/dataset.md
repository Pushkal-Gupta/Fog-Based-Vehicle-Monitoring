# Dataset Description

This document describes the **raw telemetry dataset**, **fog-computed health vectors**, and **derived decision logic** used in the Fog-Based Vehicle Monitoring System.

---

## 1. Raw Dataset from Hardware (ESP32)

The following JSON represents the **raw telemetry data** received directly from the ESP32 hardware layer.

```json
{
  "device_id": "ESP32_VEH_01",
  "vehicle_id": "VIT_CAR_001",
  "timestamp_ms": 1707051123456,
  
  "engine_oil_temp_c": 92.4,
  "transmission_temp_c": 78.1,
  "brake_temp_c": 185.6,
  "radiator_temp_c": 88.9,
  
  "motor_rpm": 3120,
  
  "vehicle_speed_kmph": 72.4,
  "fuel_efficiency_kmpl": 14.6,
  
  "battery_voltage_v": 12.6,
  "battery_health_pct": 87,
  
  "fuel_level_pct": 42,
  
  "cabin_humidity_pct": 54.2,
  "cabin_temp_c": 31.5,
  
  "tire_pressure_fl_kpa": 230,
  "tire_pressure_fr_kpa": 228,
  "tire_pressure_rl_kpa": 225,
  "tire_pressure_rr_kpa": 227,
  
  "gyro_x_dps": 0.12,
  "gyro_y_dps": -0.04,
  "gyro_z_dps": 0.98,
  
  "ambient_pressure_kpa": 101.3,
  
  "output_voltage_v": 13.9,
  
  "engine_rpm_variance": 182.4,
  "brake_temp_rise_rate": 4.6,
  "vibration_rms": 0.84,
  "dominant_vibration_hz": 142,
  
  "engine_knock_prob": 0.12,
  "engine_misfire_index": 0.04,
  "engine_load_pct": 68,
  
  "brake_pad_remaining_pct": 34,
  "brake_disc_score": 0.71,
  
  "engine_rul_pct": 62,
  "brake_rul_pct": 28,
  "battery_rul_pct": 74,
}
```

---

## 2. Fog-Computed Health Vector

The following structured health vector is computed at the fog layer from raw telemetry.

```json
{
  "meta": {
    "device_id": "ESP32_VEH_01",
    "vehicle_id": "VIT_CAR_001",
    "timestamp_ms": 1707051123456,
    "processing_node": "vehicular_fog",
    "schema_version": "v1.2"
  },

  "thermal_state": {
    "engine_oil_temp_c": 92.4,
    "transmission_temp_c": 78.1,
    "brake_temp_c": 185.6,
    "radiator_temp_c": 88.9,
    "brake_temp_rise_rate_c_per_s": 4.6,
    "thermal_stress_index": 0.82,
    "thermal_brake_margin": -0.21,
    "thermal_engine_margin": 0.34
  },

  "powertrain_state": {
    "motor_rpm": 3120,
    "engine_rpm_variance": 182.4,
    "engine_load_pct": 68,
    "engine_knock_prob": 0.12,
    "engine_misfire_index": 0.04
  },

  "electrical_state": {
    "battery_voltage_v": 12.6,
    "output_voltage_v": 13.9,
    "battery_health_pct": 87,
    "charging_status": "normal",
    "electrical_charging_efficiency_score": 0.81
  },

  "braking_state": {
    "brake_pad_remaining_pct": 34,
    "brake_disc_score": 0.71,
    "brake_health_index": 0.39
  },

  "tires_state": {
    "pressure_kpa": {
      "fl": 230,
      "fr": 228,
      "rl": 225,
      "rr": 227
    },
    "pressure_variance_kpa": 5
  },

  "motion_state": {
    "vehicle_speed_kmph": 72.4,
    "gyro_dps": {
      "x": 0.12,
      "y": -0.04,
      "z": 0.98
    },
    "vibration_rms": 0.84,
    "dominant_vibration_hz": 142,
    "mechanical_vibration_anomaly_score": 0.77
  },

  "environment_state": {
    "ambient_pressure_kpa": 101.3,
    "cabin_temp_c": 31.5,
    "cabin_humidity_pct": 54.2
  },

  "lifecycle_state": {
    "engine_rul_pct": 62,
    "brake_rul_pct": 28,
    "battery_rul_pct": 74
  },

  "global_health": {
    "vehicle_health_score": 0.64
  },

  "fog_decision": {
    "critical_class": 1,
    "actuation_triggered": 1,
    "decision_confidence": 0.93
  },

  "actuation_state": {
    "actuation_limit_vehicle_speed_kph": 40,
    "actuation_disable_aggressive_braking": true,
    "actuation_enable_brake_cooling_fan": true
  }
}
```

---

## 3. Computation Formulas

### 3.1 Thermal Stress Index

```text
normalized_temp = brake_temp_c / BRAKE_MAX_TEMP
normalized_rise = brake_temp_rise_rate / MAX_SAFE_RISE

thermal_stress_index =
clamp(0.7 * normalized_temp + 0.3 * normalized_rise, 0, 1)
```

### 3.2 Brake Health Index

```text
pad_factor = brake_pad_remaining_pct / 100
disc_factor = brake_disc_score

brake_health_index =
clamp(0.6 * pad_factor + 0.4 * disc_factor, 0, 1)
```

| Threshold | Status                      |
| :-------- | :-------------------------- |
| `< 0.4`   | End-of-life zone            |
| `< 0.3`   | Unsafe under thermal stress |

### 3.3 Charging Status Logic

```text
if output_voltage_v between 13.5 and 14.4
and battery_voltage_v > 12.2
→ charging_status = "normal"
else → "degraded"
```

### 3.4 Vibration Analysis

```text
expected_engine_band = motor_rpm / 60
vibration_ratio = dominant_vibration_hz / expected_engine_band
```

### 3.5 Vehicle Health Score

```text
vehicle_health_score =
0.35 * engine_rul_pct +
0.45 * brake_rul_pct +
0.20 * battery_rul_pct
```

_(All values normalized to 0–1)_

The final score is subject to a penalty based on the **thermal_stress_index**.

---

## 4. Critical Decision & Actuation Logic

### 4.1 Thermal Protection

```text
thermal_protection_active = (brake_temp_c > 180)
  AND (brake_temp_rise_rate_c_per_s > 3.0)
  AND (brake_health_index < 0.4)
```

### 4.2 Brake Stress Mitigation

```text
temp_factor = clamp((brake_temp_c - 120) / (200 - 120), 0, 1)
rise_factor = clamp((brake_temp_rise_rate_c_per_s - 1.0) / (6.0 - 1.0), 0, 1)
health_factor = 1 - brake_health_index
brake_stress_confidence = clamp(0.5 * temp_factor + 0.3 * rise_factor + 0.2 * health_factor,0, 1)
brake_stress_mitigation_active = (brake_stress_confidence > 0.6)
```

### 4.3 Vibration Damping Mode

```text
vibration_risk_score = clamp(0.7 * mechanical_vibration_anomaly_score + 0.3 * (vibration_rms / 1.2),0, 1)
vibration_damping_mode_active = (vibration_risk_score > 0.65)
```

### 4.4 Predictive Service Required

```text
service_risk_score = clamp( 0.6 * (1 - brake_rul_pct / 100) + 0.4 * (1 - vehicle_health_score), 0, 1)
predictive_service_required = (service_risk_score > 0.55)
```

### 4.5 Emergency Safeguard

```text
emergency_risk_score = clamp( 0.4 * thermal_stress_index + 0.3 * vibration_risk_score + 0.3 * (1 - vehicle_health_score),0, 1)
emergency_safeguard_active = (emergency_risk_score > 0.85)
```

---

## 5. Fog → Hardware Actuation Event

```json
{
  "timestamp_ms": 1707051123456,
  "decision_origin": "fog_node",
  "cloud_dependency": false,

  "trigger_measured_brake_temp_c": 185.6,
  "trigger_brake_temp_rise_rate": 4.6,
  "trigger_brake_health_index": 0.39,

  "fog_decision_critical_class": 1,
  "fog_decision_actuation_triggered": 1,
  "fog_decision_confidence": 0.93

  "fog_thermal_protection_active": true,
  "fog_brake_stress_mitigation_active": true,
  "fog_vibration_damping_mode_active": true,
  "fog_predictive_service_required": true,
  "fog_emergency_safeguard_active": false
}
```

---

## 6. Fog → Cloud → Dashboard Output

```json
{
  "vehicle_id": "VIT_CAR_001",
  "timestamp_ms": 1707051123456,

  "fog_decision_critical_class": 1,
  "fog_decision_actuation_triggered": 1,
  "fog_decision_confidence": 0.93

  "thermal_brake_margin": -0.21,
  "thermal_engine_margin": 0.34,
  "thermal_stress_index": 0.82,

  "mechanical_vibration_anomaly_score": 0.77,
  "mechanical_dominant_fault_band_hz": 142,
  "mechanical_vibration_rms": 0.84,

  "electrical_charging_efficiency_score": 0.81,
  "electrical_battery_health_pct": 87,

  "engine_rul_pct": 62,
  "brake_rul_pct": 28,
  "battery_rul_pct": 74,

  "vehicle_health_score": 0.64

  "trigger_measured_brake_temp_c": 185.6,
  "trigger_brake_temp_rise_rate": 4.6,
  "trigger_brake_health_index": 0.39,

  "fog_thermal_protection_active": true,
  "fog_brake_stress_mitigation_active": true,
  "fog_vibration_damping_mode_active": true,
  "fog_predictive_service_required": true,
  "fog_emergency_safeguard_active": false
}
```

---

## 7. Cloud → AI → Dashboard Analytical Loop

```json
{
  "vehicle_id": "VIT_CAR_001",
  "timestamp_ms": 1707051123456,

  "fog_decision_critical_class": 1,
  "fog_decision_actuation_triggered": 1,
  "fog_decision_confidence": 0.93

  "thermal_brake_margin": -0.21,
  "thermal_engine_margin": 0.34,
  "thermal_stress_index": 0.82,

  "mechanical_vibration_anomaly_score": 0.77,
  "mechanical_dominant_fault_band_hz": 142,
  "mechanical_vibration_rms": 0.84,

  "electrical_charging_efficiency_score": 0.81,
  "electrical_battery_degradation_trend": "stable",

  "usage_driver_aggression_score": 0.58,
  "usage_stress_amplification_factor": 1.27,

  "engine_rul_pct": 62,
  "brake_rul_pct": 28,
  "battery_rul_pct": 74,

  "fog_decision_critical_class": 1,
  "fog_decision_actuation_triggered": 1

  "fault_primary": "BRAKE_THERMAL_SATURATION",
  "fault_contributing_factor": ["high_brake_temp_rise_rate","low_brake_pad_remaining","sustained_vehicle_speed"],
  "fault_failure_probability": 0.61,

  "vehicle_health_score": 0.64,

  "recommendation_service_priority": "high",
  "recommendation_suggested_action": "Brake inspection and pad replacement",
  "recommendation_safe_operating_limit_km": 120

  "trigger_measured_brake_temp_c": 185.6,
  "trigger_brake_temp_rise_rate": 4.6,
  "trigger_brake_health_index": 0.39,

  "fog_thermal_protection_active": true,
  "fog_brake_stress_mitigation_active": true,
  "fog_vibration_damping_mode_active": true,
  "fog_predictive_service_required": true,
  "fog_emergency_safeguard_active": false
}
```

---

## 8. Summary

This dataset demonstrates the complete data lifecycle of the system:

- Raw sensing at the hardware layer

- Semantic transformation at the fog layer

- Predictive inference in the AI layer

- Visualization and recommendations at the dashboard

All safety-critical decisions originate at the fog layer, ensuring deterministic and low-latency response independent of cloud connectivity.
