package com.example.fog_app

import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import com.fasterxml.jackson.module.kotlin.readValue
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import java.util.ArrayDeque
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min
import kotlin.math.pow
import kotlin.math.round
import kotlin.math.sqrt

const val BRAKE_MAX_TEMP = 220.0
const val CLOUD_URL = "https://fog-based-vehicle-monitoring.onrender.com/api/intelligence/insert"

/* ================= UTILS ================= */

fun clamp(x: Double, lo: Double = 0.0, hi: Double = 1.0) = max(lo, min(hi, x))

// SAFE extractors
fun Map<String, Any>.d(k: String, def: Double = 0.0) =
    (this[k] as? Number)?.toDouble() ?: def

fun Map<String, Any>.l(k: String, def: Long = 0L) =
    (this[k] as? Number)?.toLong() ?: def

fun Map<String, Any>.s(k: String, def: String = "unknown") =
    this[k] as? String ?: def

fun List<Double>.mean() = if (isEmpty()) 0.0 else sum() / size

fun List<Double>.variance(): Double {
    if (size <= 1) return 0.0
    val m = mean()
    return map { (it - m).pow(2) }.mean()
}

/* ================= BUFFER ================= */

class TelemetryBuffer(private val maxSamples: Int) {
    private val samples = ArrayDeque<Map<String, Any>>()

    fun push(sample: Map<String, Any>?) {
        if (sample != null) {
            if (samples.size == maxSamples) samples.removeFirst()
            samples.addLast(sample)
        }
    }

    fun full() = samples.size == maxSamples
    fun all() = samples.toList()
}

/* ================= AGGREGATION ================= */

fun aggregate(samples: List<Map<String, Any>>, samplePeriod: Double): Map<String, Any> {
    fun s(k: String) = samples.map { it.d(k) }
    val last = samples.last()
    val t0 = samples.first().l("timestamp_ms")
    val t1 = last.l("timestamp_ms")
    val dt = max((t1 - t0) / 1000.0, samplePeriod)

    return mapOf(
        "device_id" to last.s("device_id"),
        "vehicle_id" to last.s("vehicle_id"),
        "timestamp_ms" to t1,
        "brake_temp_c" to s("brake_temp_c").maxOrNull()!!,
        "brake_temp_rise_rate" to ((last.d("brake_temp_c") - samples.first().d("brake_temp_c")) / dt),
        "engine_oil_temp_c" to s("engine_oil_temp_c").mean(),
        "radiator_temp_c" to s("radiator_temp_c").mean(),
        "motor_rpm" to s("motor_rpm").mean(),
        "vibration_rms" to sqrt(s("vibration_rms").map { it * it }.mean()),
        "dominant_vibration_hz" to s("dominant_vibration_hz").mean(),
        "battery_voltage_v" to s("battery_voltage_v").mean(),
        "output_voltage_v" to s("output_voltage_v").mean(),
        "battery_health_pct" to s("battery_health_pct").mean(),
        "engine_load_pct" to s("engine_load_pct").mean()
    )
}

/* ================= HEALTH MODEL ================= */

fun computeHealth(d: Map<String, Any>): Map<String, Any> {
    val brakeTemp = d.d("brake_temp_c")
    val riseRate = d.d("brake_temp_rise_rate")
    val oilTemp = d.d("engine_oil_temp_c")
    val rpm = d.d("motor_rpm")
    val load = d.d("engine_load_pct")
    val dominantHz = d.d("dominant_vibration_hz")
    val battHealth = d.d("battery_health_pct")

    val normTemp = brakeTemp / 220.0
    val thermalStress = clamp(0.7 * normTemp + 0.3 * (riseRate / 8.0))
    
    val shaftFreq = if (rpm == 0.0) 1.0 else rpm / 60.0
    val harmonicRatio = dominantHz / shaftFreq
    val vibAnomaly = clamp(abs(harmonicRatio - round(harmonicRatio)) * 2.5)

    val engineStress = clamp(0.3 * (oilTemp / 120.0) + 0.3 * (rpm / 6000.0) + 0.4 * (load / 100.0))
    val engineRul = (1.0 - engineStress) * 100.0
    val brakeRul = (1.0 - thermalStress) * 100.0
    val batteryRul = battHealth

    val vehicleHealth = 0.35 * (engineRul / 100.0) + 0.45 * (brakeRul / 100.0) + 0.20 * (batteryRul / 100.0)

    val thermalProtection = brakeTemp > 180 || (brakeTemp > 150 && riseRate > 3.0)
    val emergency = vehicleHealth < 0.35 || thermalStress > 0.9
    val predictiveService = vehicleHealth < 0.6
    val vibrationDamping = vibAnomaly > 0.7

    val criticalClass = when {
        emergency -> 3
        thermalProtection || vibrationDamping -> 2
        predictiveService -> 1
        else -> 0
    }

    return mapOf(
        "thermal_stress" to thermalStress,
        "mechanical_risk" to vibAnomaly,
        "vehicle_health" to vehicleHealth,
        "thermal_protection" to thermalProtection,
        "emergency" to emergency,
        "predictive_service" to predictiveService,
        "vibration_damping" to vibrationDamping,
        "critical_class" to criticalClass,
        "actuation" to (criticalClass >= 1),
        "confidence" to clamp(0.8 + 0.2 * (1 - vibAnomaly))
    )
}

/* ================= PACKETS ================= */

fun buildActuationPacket(d: Map<String, Any>, h: Map<String, Any>) = mapOf(
    "timestamp_ms" to d.l("timestamp_ms"),
    "decision_origin" to "fog_node",
    "cloud_dependency" to false,

    "trigger_measured_brake_temp_c" to d.d("brake_temp_c"),
    "trigger_brake_temp_rise_rate" to d.d("brake_temp_rise_rate"),
    "trigger_brake_health_index" to h.d("vehicle_health"),

    "fog_decision_critical_class" to (h["critical_class"] as Int),
    "fog_decision_actuation_triggered" to if (h["actuation"] as Boolean) 1 else 0,
    "fog_decision_confidence" to h.d("confidence"),

    "fog_thermal_protection_active" to (h["thermal_protection"] as Boolean),
    "fog_brake_stress_mitigation_active" to (h.d("thermal_stress") > 0.6),
    "fog_vibration_damping_mode_active" to (h["vibration_damping"] as Boolean),
    "fog_predictive_service_required" to (h["predictive_service"] as Boolean),
    "fog_emergency_safeguard_active" to (h["emergency"] as Boolean)
)

fun buildCloudPacket(d: Map<String, Any>, h: Map<String, Any>): Map<String, Any> {
    val brakeTemp = d.d("brake_temp_c")
    val riseRate = d.d("brake_temp_rise_rate")
    val oilTemp = d.d("engine_oil_temp_c")
    val rpm = d.d("motor_rpm")
    val load = d.d("engine_load_pct")
    val dominantHz = d.d("dominant_vibration_hz")
    val vibRms = d.d("vibration_rms")
    val battV = d.d("battery_voltage_v")
    val outV = d.d("output_voltage_v")
    val battHealth = d.d("battery_health_pct")

    val normTemp = brakeTemp / 220.0
    val thermalStress = h.d("thermal_stress")
    val vibAnomaly = h.d("mechanical_risk")
    val vehicleHealth = h.d("vehicle_health")

    val engineRul = (1.0 - clamp(0.3 * (oilTemp / 120.0) + 0.3 * (rpm / 6000.0) + 0.4 * (load / 100.0))) * 100.0
    val brakeRul = (1.0 - thermalStress) * 100.0
    val batteryRul = battHealth

    val chargingEfficiency = if (outV in 13.5..14.4 && battV > 11.8) 1.0 else 0.6

    return mapOf(
        "vehicle_id" to d.s("vehicle_id"),
        "timestamp_ms" to d.l("timestamp_ms"),
        "fog_decision_critical_class" to (h["critical_class"] as Int),
        "fog_decision_actuation_triggered" to if (h["actuation"] as Boolean) 1 else 0,
        "fog_decision_confidence" to h.d("confidence"),

        "thermal_brake_margin" to (1.0 - normTemp),
        "thermal_engine_margin" to (1.0 - (oilTemp / 130.0)),
        "thermal_stress_index" to thermalStress,

        "mechanical_vibration_anomaly_score" to vibAnomaly,
        "mechanical_dominant_fault_band_hz" to dominantHz,
        "mechanical_vibration_rms" to vibRms,

        "electrical_charging_efficiency_score" to chargingEfficiency,
        "electrical_battery_health_pct" to battHealth,

        "engine_rul_pct" to engineRul,
        "brake_rul_pct" to brakeRul,
        "battery_rul_pct" to batteryRul,
        "vehicle_health_score" to vehicleHealth,

        "trigger_measured_brake_temp_c" to brakeTemp,
        "trigger_brake_temp_rise_rate" to riseRate,
        "trigger_brake_health_index" to (brakeRul / 100.0),

        "fog_thermal_protection_active" to (h["thermal_protection"] as Boolean),
        "fog_brake_stress_mitigation_active" to (thermalStress > 0.6),
        "fog_vibration_damping_mode_active" to (h["vibration_damping"] as Boolean),
        "fog_predictive_service_required" to (h["predictive_service"] as Boolean),
        "fog_emergency_safeguard_active" to (h["emergency"] as Boolean)
    )
}

/* ================= NETWORK ================= */

val client = OkHttpClient()
val mapper = jacksonObjectMapper()

fun getDataFromESP32(ip: String): Map<String, Any>? {
    return try {
        client.newCall(Request.Builder().url("http://$ip/next").build()).execute().use { response ->
            response.body?.string()?.let { mapper.readValue<Map<String, Any>>(it) }
        }
    } catch (e: Exception) { null }
}

fun sendToESP32(ip: String, pkt: Map<String, Any>) {
    try {
        client.newCall(
            Request.Builder()
                .url("http://$ip/flags")
                .put(mapper.writeValueAsString(pkt).toRequestBody("application/json".toMediaType()))
                .build()
        ).execute().use { }
    } catch (_: Exception) { }
}

fun sendToBackend(url: String, pkt: Map<String, Any>) {
    try {
        val body = mapper.writeValueAsString(pkt).toRequestBody("application/json".toMediaType())
        client.newCall(Request.Builder().url(url).post(body).build()).execute().use { }
    } catch (e: Exception) { }
}
