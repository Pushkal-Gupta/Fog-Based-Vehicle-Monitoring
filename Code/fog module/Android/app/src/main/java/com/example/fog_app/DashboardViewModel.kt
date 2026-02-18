package com.example.fog_app

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.google.gson.Gson
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

class DashboardViewModel : ViewModel() {

    private val _vehicleData = MutableStateFlow<VehicleData?>(null)
    val vehicleData: StateFlow<VehicleData?> = _vehicleData

    init {
        // For now, we'll use the sample data provided.
        // In a real app, you would receive this from your Python service.
        viewModelScope.launch {
            val sampleJson = """ 
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
                "decision_confidence": 0.93,
                "decision_origin": "fog_node",
                "cloud_dependency": false
              },
              "safety_flags": {
                "fog_thermal_protection_active": true,
                "fog_brake_stress_mitigation_active": true,
                "fog_vibration_damping_mode_active": true,
                "fog_predictive_service_required": true,
                "fog_emergency_safeguard_active": false
              },
              "trigger_source_data": {
                "trigger_measured_brake_temp_c": 185.6,
                "trigger_brake_temp_rise_rate": 4.6,
                "trigger_brake_health_index": 0.39
              },
              "actuation_state": {
                "actuation_limit_vehicle_speed_kph": 40,
                "actuation_disable_aggressive_braking": true,
                "actuation_enable_brake_cooling_fan": true
              }
            }
            """.trimIndent()
            _vehicleData.value = Gson().fromJson(sampleJson, VehicleData::class.java)
        }
    }
}
