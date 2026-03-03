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
        "vibration_anomaly" to s("vibration_anomaly").mean(),

        /* ---------- ELECTRICAL ---------- */
        "battery_voltage_v" to s("battery_voltage_v").mean(),
        "output_voltage_v" to s("output_voltage_v").mean(),
        "battery_health_pct" to s("battery_health_pct").mean(),

        /* ---------- LOAD ---------- */
        "engine_load_pct" to s("engine_load_pct").mean(),
        "fuel_efficiency_kmpl" to s("fuel_efficiency_kmpl").mean(),
        "vehicle_speed_kmph" to s("vehicle_speed_kmph").mean(),

        /* ---------- RUL & SCORES ---------- */
        "engine_rul_pct" to s("engine_rul_pct").mean(),
        "brake_rul_pct" to s("brake_rul_pct").mean(),
        "battery_rul_pct" to s("battery_rul_pct").mean(),
        "brake_pad_remaining_pct" to s("brake_pad_remaining_pct").mean(),
        "brake_disc_score" to s("brake_disc_score").mean()
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

    val brakeTemp = d.d("brake_temp_c")
    val riseRate = d.d("brake_temp_rise_rate")
    val padPct = d.d("brake_pad_remaining_pct")
    val discScore = d.d("brake_disc_score")
    val motorRpm = d.d("motor_rpm")
    val dominantHz = d.d("dominant_vibration_hz")
    val vibrationRms = d.d("vibration_rms")
    val anomaly = d.d("vibration_anomaly")
    val batteryHealth = d.d("battery_health_pct")
    val outV = d.d("output_voltage_v")
    val battV = d.d("battery_voltage_v")

    val engineRul = d.d("engine_rul_pct")
    val brakeRul = d.d("brake_rul_pct")
    val batteryRul = d.d("battery_rul_pct")

    /* ---------------- Thermal Stress ---------------- */

    val normalizedTemp = brakeTemp / 220.0
    val normalizedRise = riseRate / 8.0

    val thermalStress = clamp(0.7 * normalizedTemp + 0.3 * normalizedRise)

    /* ---------------- Brake Health ---------------- */

    val padFactor = padPct / 100.0
    val brakeHealth = clamp(0.6 * padFactor + 0.4 * discScore)

    /* ---------------- Charging Efficiency ---------------- */

    val chargingEfficiency =
        if (outV in 13.5..14.4 && battV > 12.2) 1.0 else 0.5

    /* ---------------- Vibration ---------------- */

    val expectedBand = if (motorRpm == 0.0) 1.0 else motorRpm / 60.0
    val vibrationRatio = dominantHz / expectedBand

    val vibrationRisk = clamp(
        0.7 * anomaly + 0.3 * (vibrationRms / 1.2)
    )

    /* ---------------- Vehicle Health ---------------- */

    var vehicleHealth =
        0.35 * (engineRul / 100.0) +
        0.45 * (brakeRul / 100.0) +
        0.20 * (batteryRul / 100.0)

    vehicleHealth *= (1 - 0.25 * thermalStress) // penalty

    /* ---------------- Decisions ---------------- */

    val thermalProtection =
        brakeTemp > 180 &&
        riseRate > 3.0 &&
        brakeHealth < 0.4

    val tempFactor = clamp((brakeTemp - 120) / 80.0)
    val riseFactor = clamp((riseRate - 1.0) / 5.0)
    val healthFactor = 1 - brakeHealth

    val brakeStressConfidence =
        clamp(0.5 * tempFactor + 0.3 * riseFactor + 0.2 * healthFactor)

    val brakeMitigation = brakeStressConfidence > 0.6

    val vibrationDamping = vibrationRisk > 0.65

    val serviceRisk =
        clamp(0.6 * (1 - brakeRul / 100.0) + 0.4 * (1 - vehicleHealth))

    val predictiveService = serviceRisk > 0.55

    val emergencyRisk =
        clamp(0.4 * thermalStress + 0.3 * vibrationRisk + 0.3 * (1 - vehicleHealth))

    val emergency = emergencyRisk > 0.85

    /* ---------------- Critical Classification ---------------- */

    val criticalClass =
        when {
            emergency -> 3
            thermalProtection || vibrationDamping -> 2
            predictiveService -> 1
            else -> 0
        }

    val actuationTriggered = criticalClass >= 2

    val confidence =
        clamp(
            0.4 * thermalStress +
            0.3 * vibrationRisk +
            0.3 * (1 - vehicleHealth)
        )

    /* ---------------- Final Payload ---------------- */

    return mapOf(
        "vehicle_id" to d.s("vehicle_id"),
        "timestamp_ms" to d.l("timestamp_ms"),

        "fog_decision_critical_class" to criticalClass,
        "fog_decision_actuation_triggered" to if (actuationTriggered) 1 else 0,
        "fog_decision_confidence" to confidence,

        "thermal_brake_margin" to (1 - normalizedTemp),
        "thermal_engine_margin" to (1 - thermalStress),
        "thermal_stress_index" to thermalStress,

        "mechanical_vibration_anomaly_score" to anomaly,
        "mechanical_dominant_fault_band_hz" to dominantHz,
        "mechanical_vibration_rms" to vibrationRms,

        "electrical_charging_efficiency_score" to chargingEfficiency,
        "electrical_battery_health_pct" to batteryHealth,

        "engine_rul_pct" to engineRul,
        "brake_rul_pct" to brakeRul,
        "battery_rul_pct" to batteryRul,

        "vehicle_health_score" to vehicleHealth,

        "trigger_measured_brake_temp_c" to brakeTemp,
        "trigger_brake_temp_rise_rate" to riseRate,
        "trigger_brake_health_index" to brakeHealth,

        "fog_thermal_protection_active" to thermalProtection,
        "fog_brake_stress_mitigation_active" to brakeMitigation,
        "fog_vibration_damping_mode_active" to vibrationDamping,
        "fog_predictive_service_required" to predictiveService,
        "fog_emergency_safeguard_active" to emergency
    )
}


/* ================= NETWORK ================= */

val client = OkHttpClient()
val mapper = jacksonObjectMapper()

fun getDataFromESP32(ip: String): Map<String, Any>? {
    return try {
        println("Fetching data from ESP32")

        client.newCall(Request.Builder().url("http://$ip/next").build()).execute().use { response ->

            val bodyString = response.body?.string()

            if (bodyString == null) {
                println("Response body is null")
                return null
            }

            println("Raw Response: $bodyString")

            val parsedData: Map<String, Any> = mapper.readValue(bodyString)
            parsedData
        }

    } catch (e: Exception) {
        println("Error: ${e.message}")
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
        println("Sending to cloud ... ")

        client.newCall(
            Request.Builder()
                .url(url)
                .post(
                    mapper.writeValueAsString(pkt)
                        .toRequestBody("application/json".toMediaType())
                )
                .build()
        ).execute().use { response ->

            println("Response Code: ${response.code}")

            val responseBody = response.body?.string()

            if (responseBody != null) {
                println("Response Body: $responseBody")
            } else {
                println("Response body is null")
            }
        }

    } catch (e: Exception) {
        println("Cloud send failed: ${e.message}")
    }
}
