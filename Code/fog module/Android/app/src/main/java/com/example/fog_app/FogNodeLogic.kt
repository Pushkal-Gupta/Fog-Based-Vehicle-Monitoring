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

// SAFE extractors (no more !! explosions)
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

// prevent divide-by-zero physics
    val dt = max((t1 - t0) / 1000.0, samplePeriod)

    val rpmSeries = s("motor_rpm")

    return mapOf(
        "device_id" to last.s("device_id"),
        "vehicle_id" to last.s("vehicle_id"),
        "timestamp_ms" to t1,

        /* ---------- THERMAL ---------- */
        "brake_temp_c" to s("brake_temp_c").maxOrNull()!!,
        "brake_temp_rise_rate" to (
                (samples.last().d("brake_temp_c") - samples.first().d("brake_temp_c")) / dt
                ),
        "engine_oil_temp_c" to s("engine_oil_temp_c").mean(),
        "radiator_temp_c" to s("radiator_temp_c").mean(),

        /* ---------- MECHANICAL ---------- */
        "motor_rpm" to rpmSeries.mean(),
        "engine_rpm_variance" to rpmSeries.variance(),
        "vibration_rms" to sqrt(s("vibration_rms").map { it * it }.mean()),
        "dominant_vibration_hz" to s("dominant_vibration_hz").mean(),

        /* ---------- ELECTRICAL ---------- */
        "battery_voltage_v" to s("battery_voltage_v").mean(),
        "output_voltage_v" to s("output_voltage_v").mean(),
        "battery_health_pct" to s("battery_health_pct").mean(),

        /* ---------- LOAD ---------- */
        "engine_load_pct" to s("engine_load_pct").mean(),
        "fuel_efficiency_kmpl" to s("fuel_efficiency_kmpl").mean(),
        "vehicle_speed_kmph" to s("vehicle_speed_kmph").mean()
    )

}
/* ================= HEALTH MODEL ================= */

fun computeHealth(d: Map<String, Any>): Map<String, Any> {

    val rpm = d.d("motor_rpm")
    val shaftFreq = if (rpm == 0.0) 1.0 else rpm / 60.0

    /* ---------- THERMAL STRESS ---------- */
    val brakeStress = clamp(d.d("brake_temp_c") / 220.0)
    val oilStress = clamp(d.d("engine_oil_temp_c") / 130.0)
    val coolingDelta = clamp((d.d("engine_oil_temp_c") - d.d("radiator_temp_c")) / 40.0)

    val thermalStress =
        0.5 * brakeStress +
                0.3 * oilStress +
                0.2 * coolingDelta

    /* ---------- MECHANICAL RISK ---------- */
    val harmonicRatio = d.d("dominant_vibration_hz") / shaftFreq
    val freqAnomaly = abs(harmonicRatio - round(harmonicRatio))

    val mechanicalRisk =
        0.6 * clamp(freqAnomaly * 2) +
                0.4 * clamp(d.d("vibration_rms") / 2.0)

    /* ---------- ELECTRICAL RISK ---------- */
    val chargingEfficiency =
        if (d.d("battery_voltage_v") == 0.0) 0.0
        else d.d("output_voltage_v") / d.d("battery_voltage_v")

    val electricalRisk = clamp(1 - chargingEfficiency)

    /* ---------- LOAD STRESS ---------- */
    val loadStress =
        0.5 * (d.d("engine_load_pct") / 100.0) +
                0.5 * clamp((rpm / 6000.0) * (1 - d.d("fuel_efficiency_kmpl") / 20.0))

    /* ---------- FINAL VEHICLE HEALTH ---------- */
    val vehicleHealth = clamp(
        1 - (
                0.35 * thermalStress +
                        0.30 * mechanicalRisk +
                        0.20 * electricalRisk +
                        0.15 * loadStress
                )
    )

    val thermalProtection =
        d.d("brake_temp_c") > 180 &&
                d.d("brake_temp_rise_rate") > 2.5

    val emergency = vehicleHealth < 0.35
    val actuation = thermalProtection || emergency

    return mapOf(
        "thermal_stress" to thermalStress,
        "mechanical_risk" to mechanicalRisk,
        "electrical_risk" to electricalRisk,
        "load_stress" to loadStress,
        "vehicle_health" to vehicleHealth,
        "thermal_protection" to thermalProtection,
        "emergency" to emergency,
        "actuation" to actuation,
        "confidence" to (0.7 + 0.3 * (1 - mechanicalRisk))
    )

}

/* ================= PACKETS ================= */

fun buildActuationPacket(d: Map<String, Any>, h: Map<String, Any>) = mapOf(
    "timestamp_ms" to d["timestamp_ms"]!!,
    "decision_origin" to "fog_node",
    "cloud_dependency" to false,
    "trigger_measured_brake_temp_c" to d["brake_temp_c"]!!,
    "trigger_brake_temp_rise_rate" to d["brake_temp_rise_rate"]!!,
    "fog_decision_critical_class" to if (h["thermal_protection"] as Boolean) 1 else 0,
    "fog_decision_actuation_triggered" to if (h["actuation"] as Boolean) 1 else 0,
    "fog_decision_confidence" to h["confidence"]!!,
    "fog_thermal_protection_active" to h["thermal_protection"]!!,
    "fog_vibration_damping_mode_active" to h["emergency"]!!,
    "fog_predictive_service_required" to ((h["vehicle_health"] as Double) < 0.5),
    "fog_emergency_safeguard_active" to h["emergency"]!!
)

fun buildCloudPacket(d: Map<String, Any>, h: Map<String, Any>): Map<String, Any> {

    val brakeMargin = clamp((BRAKE_MAX_TEMP - d.d("brake_temp_c")) / BRAKE_MAX_TEMP)
    val engineMargin = clamp((140 - d.d("engine_oil_temp_c")) / 140)
    val chargingEfficiency =
        if (d.d("battery_voltage_v") == 0.0) 0.0
        else clamp(d.d("output_voltage_v") / d.d("battery_voltage_v"))

    val expectedBand = if (d.d("motor_rpm") == 0.0) 1.0 else d.d("motor_rpm") / 60
    val vibrationRatio = d.d("dominant_vibration_hz") / expectedBand
    val vibrationAnomaly = clamp(abs(vibrationRatio - round(vibrationRatio)))

    return mapOf(
        "vehicle_id" to d["vehicle_id"]!!,
        "timestamp_ms" to d["timestamp_ms"]!!,
        "thermal_brake_margin" to brakeMargin,
        "thermal_engine_margin" to engineMargin,
        "thermal_stress_index" to h["thermal_stress"]!!,
        "mechanical_vibration_anomaly_score" to vibrationAnomaly,
        "mechanical_dominant_fault_band_hz" to d["dominant_vibration_hz"]!!,
        "mechanical_vibration_rms" to d["vibration_rms"]!!,
        "electrical_charging_efficiency_score" to chargingEfficiency,
        "electrical_battery_health_pct" to d["battery_health_pct"]!!,
        "vehicle_health_score" to h["vehicle_health"]!!
    )

}


/* ================= NETWORK ================= */

val client = OkHttpClient()
val mapper = jacksonObjectMapper()

fun getDataFromESP32(ip: String): Map<String, Any>? {
    return try {
        client.newCall(Request.Builder().url("http://$ip/next").build()).execute().use {
            mapper.readValue(it.body!!.string())
        }
    } catch (_: Exception) {
        null
    }
}

fun sendToESP32(ip: String, pkt: Map<String, Any>) {
    try {
        client.newCall(
            Request.Builder()
                .url("http://$ip/flags")
                .put(mapper.writeValueAsString(pkt).toRequestBody("application/json".toMediaType()))
                .build()
        ).execute().use { }
    } catch (_: Exception) {
    }
}

fun sendToBackend(url: String, pkt: Map<String, Any>) {
    try {
        client.newCall(
            Request.Builder()
                .url(url)
                .post(mapper.writeValueAsString(pkt).toRequestBody("application/json".toMediaType()))
                .build()
        ).execute().use { }
    } catch (e: Exception) {
        println("Cloud send failed: $e")
    }
}
