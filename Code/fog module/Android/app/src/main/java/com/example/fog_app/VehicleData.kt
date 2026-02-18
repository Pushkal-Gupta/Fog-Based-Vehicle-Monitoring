
package com.example.fog_app

import com.google.gson.annotations.SerializedName

data class VehicleData(
    val meta: Meta,
    @SerializedName("thermal_state")
    val thermalState: ThermalState,
    @SerializedName("powertrain_state")
    val powertrainState: PowertrainState,
    @SerializedName("electrical_state")
    val electricalState: ElectricalState,
    @SerializedName("braking_state")
    val brakingState: BrakingState,
    @SerializedName("tires_state")
    val tiresState: TiresState,
    @SerializedName("motion_state")
    val motionState: MotionState,
    @SerializedName("environment_state")
    val environmentState: EnvironmentState,
    @SerializedName("lifecycle_state")
    val lifecycleState: LifecycleState,
    @SerializedName("global_health")
    val globalHealth: GlobalHealth,
    @SerializedName("fog_decision")
    val fogDecision: FogDecision,
    @SerializedName("safety_flags")
    val safetyFlags: SafetyFlags,
    @SerializedName("trigger_source_data")
    val triggerSourceData: TriggerSourceData,
    @SerializedName("actuation_state")
    val actuationState: ActuationState
)

data class Meta(
    @SerializedName("device_id")
    val deviceId: String,
    @SerializedName("vehicle_id")
    val vehicleId: String,
    @SerializedName("timestamp_ms")
    val timestampMs: Long,
    @SerializedName("processing_node")
    val processingNode: String,
    @SerializedName("schema_version")
    val schemaVersion: String
)

data class ThermalState(
    @SerializedName("engine_oil_temp_c")
    val engineOilTempC: Double,
    @SerializedName("transmission_temp_c")
    val transmissionTempC: Double,
    @SerializedName("brake_temp_c")
    val brakeTempC: Double,
    @SerializedName("radiator_temp_c")
    val radiatorTempC: Double,
    @SerializedName("brake_temp_rise_rate_c_per_s")
    val brakeTempRiseRateCPerS: Double,
    @SerializedName("thermal_stress_index")
    val thermalStressIndex: Double,
    @SerializedName("thermal_brake_margin")
    val thermalBrakeMargin: Double,
    @SerializedName("thermal_engine_margin")
    val thermalEngineMargin: Double
)

data class PowertrainState(
    @SerializedName("motor_rpm")
    val motorRpm: Int,
    @SerializedName("engine_rpm_variance")
    val engineRpmVariance: Double,
    @SerializedName("engine_load_pct")
    val engineLoadPct: Int,
    @SerializedName("engine_knock_prob")
    val engineKnockProb: Double,
    @SerializedName("engine_misfire_index")
    val engineMisfireIndex: Double
)

data class ElectricalState(
    @SerializedName("battery_voltage_v")
    val batteryVoltageV: Double,
    @SerializedName("output_voltage_v")
    val outputVoltageV: Double,
    @SerializedName("battery_health_pct")
    val batteryHealthPct: Int,
    @SerializedName("charging_status")
    val chargingStatus: String,
    @SerializedName("electrical_charging_efficiency_score")
    val electricalChargingEfficiencyScore: Double
)

data class BrakingState(
    @SerializedName("brake_pad_remaining_pct")
    val brakePadRemainingPct: Int,
    @SerializedName("brake_disc_score")
    val brakeDiscScore: Double,
    @SerializedName("brake_health_index")
    val brakeHealthIndex: Double
)

data class TiresState(
    @SerializedName("pressure_kpa")
    val pressureKpa: Pressure,
    @SerializedName("pressure_variance_kpa")
    val pressureVarianceKpa: Int
)

data class Pressure(
    val fl: Int,
    val fr: Int,
    val rl: Int,
    val rr: Int
)

data class MotionState(
    @SerializedName("vehicle_speed_kmph")
    val vehicleSpeedKmph: Double,
    @SerializedName("gyro_dps")
    val gyroDps: Gyro,
    @SerializedName("vibration_rms")
    val vibrationRms: Double,
    @SerializedName("dominant_vibration_hz")
    val dominantVibrationHz: Int,
    @SerializedName("mechanical_vibration_anomaly_score")
    val mechanicalVibrationAnomalyScore: Double
)

data class Gyro(
    val x: Double,
    val y: Double,
    val z: Double
)

data class EnvironmentState(
    @SerializedName("ambient_pressure_kpa")
    val ambientPressureKpa: Double,
    @SerializedName("cabin_temp_c")
    val cabinTempC: Double,
    @SerializedName("cabin_humidity_pct")
    val cabinHumidityPct: Double
)

data class LifecycleState(
    @SerializedName("engine_rul_pct")
    val engineRulPct: Int,
    @SerializedName("brake_rul_pct")
    val brakeRulPct: Int,
    @SerializedName("battery_rul_pct")
    val batteryRulPct: Int
)

data class GlobalHealth(
    @SerializedName("vehicle_health_score")
    val vehicleHealthScore: Double
)

data class FogDecision(
    @SerializedName("critical_class")
    val criticalClass: Int,
    @SerializedName("actuation_triggered")
    val actuationTriggered: Int,
    @SerializedName("decision_confidence")
    val decisionConfidence: Double,
    @SerializedName("decision_origin")
    val decisionOrigin: String,
    @SerializedName("cloud_dependency")
    val cloudDependency: Boolean
)

data class SafetyFlags(
    @SerializedName("fog_thermal_protection_active")
    val fogThermalProtectionActive: Boolean,
    @SerializedName("fog_brake_stress_mitigation_active")
    val fogBrakeStressMitigationActive: Boolean,
    @SerializedName("fog_vibration_damping_mode_active")
    val fogVibrationDampingModeActive: Boolean,
    @SerializedName("fog_predictive_service_required")
    val fogPredictiveServiceRequired: Boolean,
    @SerializedName("fog_emergency_safeguard_active")
    val fogEmergencySafeguardActive: Boolean
)

data class TriggerSourceData(
    @SerializedName("trigger_measured_brake_temp_c")
    val triggerMeasuredBrakeTempC: Double,
    @SerializedName("trigger_brake_temp_rise_rate")
    val triggerBrakeTempRiseRate: Double,
    @SerializedName("trigger_brake_health_index")
    val triggerBrakeHealthIndex: Double
)

data class ActuationState(
    @SerializedName("actuation_limit_vehicle_speed_kph")
    val actuationLimitVehicleSpeedKph: Int,
    @SerializedName("actuation_disable_aggressive_braking")
    val actuationDisableAggressiveBraking: Boolean,
    @SerializedName("actuation_enable_brake_cooling_fan")
    val actuationEnableBrakeCoolingFan: Boolean
)
