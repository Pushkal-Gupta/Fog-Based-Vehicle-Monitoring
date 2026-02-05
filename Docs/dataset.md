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

  "driver_aggression_score": 0.58,

  "engine_rul_pct": 62,
  "brake_rul_pct": 28,
  "battery_rul_pct": 74,

  "vehicle_health_score": 0.64,

  "alert_level": "critical",
  "alert_code": "BRAKE_OVERHEAT"
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
    "schema_version": "v1.0"
  },

  "thermal_state": {
    "engine_oil_temp_c": 92.4,
    "transmission_temp_c": 78.1,
    "brake_temp_c": 185.6,
    "radiator_temp_c": 88.9,
    "brake_temp_rise_rate_c_per_s": 4.6,
    "thermal_stress_index": 0.82
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
    "charging_status": "normal"
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
    "gyro_dps": {
      "x": 0.12,
      "y": -0.04,
      "z": 0.98
    },
    "vibration_rms": 0.84,
    "dominant_vibration_hz": 142
  },

  "environment_state": {
    "ambient_pressure_kpa": 101.3,
    "cabin_temp_c": 31.5,
    "cabin_humidity_pct": 54.2
  },

  "driver_state": {
    "driver_aggression_score": 0.58
  },

  "lifecycle_state": {
    "engine_rul_pct": 62,
    "brake_rul_pct": 28,
    "battery_rul_pct": 74
  },

  "global_health": {
    "vehicle_health_score": 0.64,
    "alert_level": "critical",
    "alert_code": "BRAKE_OVERHEAT"
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

### 4.1 Critical Condition

```text
IF brake_temp_c > 180
AND brake_temp_rise_rate > 3.0
AND brake_health_index < 0.4
→ CRITICAL
```

### 4.2 Confidence Calculation

```text
confidence =
clamp(
0.5 * temp_factor +
0.3 * rise_factor +
0.2 * (1 - brake_health_index),
0, 1
)
```

### 4.3 Immediate Action

```text
→ speed_limit = 40
→ disable aggressive braking
→ enable cooling
```

---

## 5. Fog → Hardware Actuation Event

```json
{
  "event_type": "SAFETY_CRITICAL",
  "timestamp_ms": 1707051123456,
  "decision_origin": "fog_node",
  "cloud_dependency": false,

  "trigger": {
    "subsystem": "braking",
    "condition": "thermal_runaway",
    "measured_value": 185.6,
    "rate_of_change": 4.6,
    "threshold_exceeded": true
  },

  "decision": {
    "action_required": true,
    "action_code": "BRAKE_COOLING_MODE",
    "severity": "IMMEDIATE"
  },

  "actuation_commands": {
    "limit_vehicle_speed_kph": 40,
    "disable_aggressive_braking": true,
    "enable_brake_cooling_fan": true,
    "driver_alert": {
      "type": "audio_visual",
      "message": "Brake overheating. Reduce speed immediately."
    }
  },

  "confidence": 0.93
}
```

---

## 6. Fog → Cloud → AI → Dashboard Output

```json
{
  "vehicle_id": "VIT_CAR_001",
  "timestamp_ms": 1707051123456,

  "health_vectors": {
    "thermal": {
      "brake_thermal_margin": -0.21,
      "engine_thermal_margin": 0.34
    },
    "mechanical": {
      "vibration_anomaly_score": 0.77,
      "dominant_fault_band_hz": 142
    },
    "electrical": {
      "charging_efficiency_score": 0.81,
      "battery_degradation_trend": "stable"
    },
    "usage_behavior": {
      "driver_aggression_score": 0.58,
      "stress_amplification_factor": 1.27
    }
  },

  "rul_estimates": {
    "engine_rul_pct": 62,
    "brake_rul_pct": 28,
    "battery_rul_pct": 74
  },

  "fault_inference": {
    "primary_fault": "BRAKE_THERMAL_SATURATION",
    "contributing_factors": [
      "high_brake_temp_rise_rate",
      "low_brake_pad_remaining",
      "moderate_driver_aggression"
    ],
    "failure_probability_7d": 0.61
  },

  "vehicle_health_score": 0.64,

  "recommendations": {
    "service_priority": "high",
    "suggested_action": "Brake inspection and pad replacement",
    "safe_operating_limit_km": 120
  }
}
```

---

## 7. Summary

This dataset demonstrates the complete data lifecycle of the system:

- Raw sensing at the hardware layer

- Semantic transformation at the fog layer

- Predictive inference in the AI layer

- Visualization and recommendations at the dashboard

All safety-critical decisions originate at the fog layer, ensuring deterministic and low-latency response independent of cloud connectivity.
