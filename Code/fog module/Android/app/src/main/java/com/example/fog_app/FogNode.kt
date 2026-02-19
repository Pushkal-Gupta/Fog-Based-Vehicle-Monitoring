package com.example.fog_app

import kotlin.concurrent.thread
import kotlin.math.*
import java.util.ArrayDeque
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import com.fasterxml.jackson.module.kotlin.readValue

/* ================= CONFIG ================= */

const val SAMPLE_PERIOD = 0.025
const val WINDOW_SEC = 1.0
const val MAX_SAMPLES = (WINDOW_SEC / SAMPLE_PERIOD).toInt()

const val BRAKE_MAX_TEMP = 220.0
const val MAX_SAFE_RISE = 6.0

const val ESP32_IP = "192.168.219.78"
const val CLOUD_URL = "https://fog-based-vehicle-monitoring.onrender.com/api/intelligence/insert"

/* ================= UTILS ================= */

fun clamp(x: Double, lo: Double = 0.0, hi: Double = 1.0) = max(lo, min(hi, x))
fun Map<String, Any>.d(k: String) = (this[k] as Number).toDouble()
fun Map<String, Any>.l(k: String) = (this[k] as Number).toLong()

fun List<Double>.mean() = if (isEmpty()) 0.0 else sum() / size
fun List<Double>.variance(): Double {
    if (size <= 1) return 0.0
    val m = mean()
    return map { (it - m).pow(2) }.mean()
}

/* ================= BUFFER ================= */

class TelemetryBuffer {
    private val samples = ArrayDeque<Map<String, Any>>()

    fun push(sample: Map<String, Any>?) {
        if (sample != null) {
            if (samples.size == MAX_SAMPLES) samples.removeFirst()
            samples.addLast(sample)
        }
    }

    fun full() = samples.size == MAX_SAMPLES
    fun all() = samples.toList()
}

/* ================= AGGREGATION ================= */

fun aggregate(samples: List<Map<String, Any>>): Map<String, Any> {

    fun s(k: String) = samples.map { it.d(k) }
    val last = samples.last()

    val t0 = samples.first().l("timestamp_ms")
    val t1 = last.l("timestamp_ms")
    val dt = if (t1 != t0) (t1 - t0) / 1000.0 else 1.0

    val rpmSeries = s("motor_rpm")

    return mapOf(
        "device_id" to last["device_id"]!!,
        "vehicle_id" to last["vehicle_id"]!!,
        "timestamp_ms" to t1,

        "brake_temp_c" to s("brake_temp_c").maxOrNull()!!,
        "brake_temp_rise_rate" to ((samples.last().d("brake_temp_c") - samples.first().d("brake_temp_c")) / dt),

        "engine_oil_temp_c" to s("engine_oil_temp_c").mean(),
        "motor_rpm" to rpmSeries.mean(),
        "engine_rpm_variance" to rpmSeries.variance(),

        "vibration_rms" to sqrt(s("vibration_rms").map { it*it }.mean()),
        "dominant_vibration_hz" to s("dominant_vibration_hz").mean(),

        "battery_voltage_v" to s("battery_voltage_v").mean(),
        "output_voltage_v" to s("output_voltage_v").mean(),
        "battery_health_pct" to last["battery_health_pct"]!!,

        "engine_rul_pct" to last["engine_rul_pct"]!!,
        "brake_rul_pct" to last["brake_rul_pct"]!!,
        "battery_rul_pct" to last["battery_rul_pct"]!!,

        "brake_pad_remaining_pct" to last["brake_pad_remaining_pct"]!!,
        "brake_disc_score" to last["brake_disc_score"]!!
    )
}

/* ================= HEALTH MODEL ================= */

fun computeHealth(d: Map<String, Any>): Map<String, Any> {

    val thermalStress = clamp(
        0.7*(d.d("brake_temp_c")/BRAKE_MAX_TEMP) +
        0.3*(d.d("brake_temp_rise_rate")/MAX_SAFE_RISE)
    )

    val brakeHealth = clamp(
        0.6*(d.d("brake_pad_remaining_pct")/100)+
        0.4*d.d("brake_disc_score")
    )

    var vehicleHealth =
        0.35*(d.d("engine_rul_pct")/100)+
        0.45*(d.d("brake_rul_pct")/100)+
        0.20*(d.d("battery_rul_pct")/100)

    vehicleHealth *= (1-0.4*thermalStress)

    val expectedBand = if (d.d("motor_rpm")==0.0) 1.0 else d.d("motor_rpm")/60
    val vibrationRatio = d.d("dominant_vibration_hz")/expectedBand
    val vibrationRisk = clamp(0.7*(vibrationRatio/2.5)+0.3*(d.d("vibration_rms")/1.2))

    val thermalProtection =
        d.d("brake_temp_c")>180 &&
        d.d("brake_temp_rise_rate")>3 &&
        brakeHealth<0.4

    val emergency =
        clamp(0.4*thermalStress + 0.3*vibrationRisk + 0.3*(1-vehicleHealth))>0.85

    val actuation = thermalProtection || emergency

    return mapOf(
        "thermal_stress" to thermalStress,
        "brake_health" to brakeHealth,
        "vehicle_health" to vehicleHealth,
        "thermal_protection" to thermalProtection,
        "emergency" to emergency,
        "actuation" to actuation,
        "confidence" to ((0.6+0.4*thermalStress)*100).roundToInt()/100.0
    )
}

/* ================= PACKETS ================= */

fun buildActuationPacket(d: Map<String, Any>, h: Map<String, Any>) = mapOf(
    "timestamp_ms" to d["timestamp_ms"]!!,
    "decision_origin" to "fog_node",
    "cloud_dependency" to false,
    "trigger_measured_brake_temp_c" to d["brake_temp_c"]!!,
    "trigger_brake_temp_rise_rate" to d["brake_temp_rise_rate"]!!,
    "trigger_brake_health_index" to h["brake_health"]!!,
    "fog_decision_critical_class" to if (h["thermal_protection"] as Boolean) 1 else 0,
    "fog_decision_actuation_triggered" to if (h["actuation"] as Boolean) 1 else 0,
    "fog_decision_confidence" to h["confidence"]!!,
    "fog_thermal_protection_active" to h["thermal_protection"]!!,
    "fog_brake_stress_mitigation_active" to h["thermal_protection"]!!,
    "fog_vibration_damping_mode_active" to h["emergency"]!!,
    "fog_predictive_service_required" to ((h["vehicle_health"] as Double) < 0.5),
    "fog_emergency_safeguard_active" to h["emergency"]!!
)

fun buildCloudPacket(d: Map<String, Any>, h: Map<String, Any>): Map<String, Any> {

    val brakeMargin = clamp((BRAKE_MAX_TEMP-d.d("brake_temp_c"))/BRAKE_MAX_TEMP)
    val engineMargin = clamp((140-d.d("engine_oil_temp_c"))/140)
    val chargingEfficiency = if (d.d("battery_voltage_v")==0.0) 0.0 else clamp(d.d("output_voltage_v")/d.d("battery_voltage_v"))

    val expectedBand = if (d.d("motor_rpm")==0.0) 1.0 else d.d("motor_rpm")/60
    val vibrationRatio = d.d("dominant_vibration_hz")/expectedBand
    val vibrationAnomaly = clamp(vibrationRatio/2.5)

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
        "engine_rul_pct" to d["engine_rul_pct"]!!,
        "brake_rul_pct" to d["brake_rul_pct"]!!,
        "battery_rul_pct" to d["battery_rul_pct"]!!,
        "vehicle_health_score" to h["vehicle_health"]!!
    )
}

/* ================= NETWORK ================= */

val client = OkHttpClient()
val mapper = jacksonObjectMapper()

fun getDataFromESP32(): Map<String, Any>? =
    try { mapper.readValue(client.newCall(Request.Builder().url("http://$ESP32_IP/data").build()).execute().body!!.string()) }
    catch(_:Exception){ null }

fun sendToESP32(pkt: Map<String, Any>) =
    try { client.newCall(Request.Builder().url("http://$ESP32_IP/actuate").put(RequestBody.create("application/json".toMediaType(),mapper.writeValueAsString(pkt))).build()).execute() }
    catch(_:Exception){}

fun sendToBackend(pkt: Map<String, Any>) =
    try { client.newCall(Request.Builder().url(CLOUD_URL).post(RequestBody.create("application/json".toMediaType(),mapper.writeValueAsString(pkt))).build()).execute() }
    catch(e:Exception){ println("Cloud send failed: $e") }

/* ================= MAIN LOOP ================= */

fun mainLoop(){

    val buffer=TelemetryBuffer()
    var nextTick=System.nanoTime()
    var lastCloud=System.nanoTime()

    while(true){

        buffer.push(getDataFromESP32())

        if(buffer.full()){
            val agg=aggregate(buffer.all())
            val health=computeHealth(agg)

            if(health["actuation"] as Boolean){
                sendToESP32(buildActuationPacket(agg,health))
                sendToBackend(buildCloudPacket(agg,health))
                lastCloud=System.nanoTime()
            }
            else if((System.nanoTime()-lastCloud)/1e9>=1){
                sendToBackend(buildCloudPacket(agg,health))
                lastCloud=System.nanoTime()
            }
        }

        nextTick+=(SAMPLE_PERIOD*1e9).toLong()
        val sleep=nextTick-System.nanoTime()
        if(sleep>0) Thread.sleep(sleep/1_000_000)
    }
}

fun main(){
    println("Fog node running")
    thread(start=true,isDaemon=false){ mainLoop() }
}
