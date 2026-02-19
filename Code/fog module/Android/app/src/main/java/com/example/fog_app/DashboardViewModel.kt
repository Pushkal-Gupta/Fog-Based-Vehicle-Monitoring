package com.example.fog_app

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.google.gson.Gson
import com.google.gson.GsonBuilder
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

class DashboardViewModel : ViewModel() {

    private val _vehicleData = MutableStateFlow<VehicleData?>(null)
    val vehicleData: StateFlow<VehicleData?> = _vehicleData
    private var rawJson: String = ""

    fun getRawJson(): String {
        return rawJson
    }

    fun getDataForCategory(category: String): List<Pair<String, Float>> {
        return when (category) {
            "Thermal State" -> thermalStateData
            "Powertrain State" -> powertrainStateData
            "Electrical State" -> electricalStateData
            "Braking State" -> brakingStateData
            "Tires State" -> tiresStateData
            "Motion State" -> motionStateData
            "Environment State" -> environmentStateData
            "Lifecycle State" -> lifecycleStateData
            "Global Health" -> globalHealthData
            else -> emptyList()
        }
    }

    val thermalStateData: List<Pair<String, Float>>
        get() = _vehicleData.value?.thermalState?.let {
            listOf(
                "Engine Oil" to it.engineOilTempC.toFloat(),
                "Transmission" to it.transmissionTempC.toFloat(),
                "Brake" to it.brakeTempC.toFloat(),
                "Radiator" to it.radiatorTempC.toFloat()
            )
        } ?: emptyList()

    val powertrainStateData: List<Pair<String, Float>>
        get() = _vehicleData.value?.powertrainState?.let {
            listOf(
                "Motor RPM" to it.motorRpm.toFloat(),
                "RPM Variance" to it.engineRpmVariance.toFloat(),
                "Engine Load" to it.engineLoadPct.toFloat(),
            )
        } ?: emptyList()

    val electricalStateData: List<Pair<String, Float>>
        get() = _vehicleData.value?.electricalState?.let {
            listOf(
                "Battery V" to it.batteryVoltageV.toFloat(),
                "Output V" to it.outputVoltageV.toFloat(),
                "Battery Health" to it.batteryHealthPct.toFloat(),
            )
        } ?: emptyList()

    val brakingStateData: List<Pair<String, Float>>
        get() = _vehicleData.value?.brakingState?.let {
            listOf(
                "Pad Remaining" to it.brakePadRemainingPct.toFloat(),
                "Disc Score" to it.brakeDiscScore.toFloat(),
                "Health Index" to it.brakeHealthIndex.toFloat(),
            )
        } ?: emptyList()

    val tiresStateData: List<Pair<String, Float>>
        get() = _vehicleData.value?.tiresState?.pressureKpa?.let {
            listOf(
                "FL" to it.fl.toFloat(),
                "FR" to it.fr.toFloat(),
                "RL" to it.rl.toFloat(),
                "RR" to it.rr.toFloat(),
            )
        } ?: emptyList()

    val motionStateData: List<Pair<String, Float>>
        get() = _vehicleData.value?.motionState?.let {
            listOf(
                "Speed" to it.vehicleSpeedKmph.toFloat(),
                "Vibration" to it.vibrationRms.toFloat(),
            )
        } ?: emptyList()

    val environmentStateData: List<Pair<String, Float>>
        get() = _vehicleData.value?.environmentState?.let {
            listOf(
                "Pressure" to it.ambientPressureKpa.toFloat(),
                "Cabin Temp" to it.cabinTempC.toFloat(),
                "Humidity" to it.cabinHumidityPct.toFloat(),
            )
        } ?: emptyList()

    val lifecycleStateData: List<Pair<String, Float>>
        get() = _vehicleData.value?.lifecycleState?.let {
            listOf(
                "Engine RUL" to it.engineRulPct.toFloat(),
                "Brake RUL" to it.brakeRulPct.toFloat(),
                "Battery RUL" to it.batteryRulPct.toFloat(),
            )
        } ?: emptyList()

    val globalHealthData: List<Pair<String, Float>>
        get() = _vehicleData.value?.globalHealth?.let {
            listOf(
                "Health Score" to it.vehicleHealthScore.toFloat(),
            )
        } ?: emptyList()


    init {
        viewModelScope.launch {
            rawJson = """
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
            val gson = GsonBuilder().setPrettyPrinting().create()
            val vehicleDataJson = gson.fromJson(rawJson, VehicleData::class.java)
            _vehicleData.value = vehicleDataJson
        }
    }
}
