package com.example.fog_app

import androidx.lifecycle.ViewModel
import kotlinx.coroutines.flow.StateFlow

class DashboardViewModel : ViewModel() {

    val vehicleData: StateFlow<VehicleData?> = VehicleDataRepository.vehicleData
    val esp32Ip: StateFlow<String> = VehicleDataRepository.esp32Ip
    val samplePeriod: StateFlow<Double> = VehicleDataRepository.samplePeriod
    val windowSec: StateFlow<Double> = VehicleDataRepository.windowSec

    fun getRawJson(): String = VehicleDataRepository.rawJson.value

    fun getProcessedHealthVector(): String = VehicleDataRepository.processedHealthVector.value

    fun setEsp32Ip(ip: String) {
        VehicleDataRepository.esp32Ip.value = ip
    }

    fun setSamplePeriod(period: Double) {
        VehicleDataRepository.samplePeriod.value = period
    }

    fun setWindowSec(sec: Double) {
        VehicleDataRepository.windowSec.value = sec
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
        get() = vehicleData.value?.thermalState?.let {
            listOf(
                "Engine Oil" to it.engineOilTempC.toFloat(),
                "Transmission" to it.transmissionTempC.toFloat(),
                "Brake" to it.brakeTempC.toFloat(),
                "Radiator" to it.radiatorTempC.toFloat()
            )
        } ?: emptyList()

    val powertrainStateData: List<Pair<String, Float>>
        get() = vehicleData.value?.powertrainState?.let {
            listOf(
                "Motor RPM" to it.motorRpm.toFloat(),
                "RPM Variance" to it.engineRpmVariance.toFloat(),
                "Engine Load" to it.engineLoadPct.toFloat(),
            )
        } ?: emptyList()

    val electricalStateData: List<Pair<String, Float>>
        get() = vehicleData.value?.electricalState?.let {
            listOf(
                "Battery V" to it.batteryVoltageV.toFloat(),
                "Output V" to it.outputVoltageV.toFloat(),
                "Battery Health" to it.batteryHealthPct.toFloat(),
            )
        } ?: emptyList()

    val brakingStateData: List<Pair<String, Float>>
        get() = vehicleData.value?.brakingState?.let {
            listOf(
                "Pad Remaining" to it.brakePadRemainingPct.toFloat(),
                "Disc Score" to it.brakeDiscScore.toFloat(),
                "Health Index" to it.brakeHealthIndex.toFloat(),
            )
        } ?: emptyList()

    val tiresStateData: List<Pair<String, Float>>
        get() = vehicleData.value?.tiresState?.pressureKpa?.let {
            listOf(
                "FL" to it.fl.toFloat(),
                "FR" to it.fr.toFloat(),
                "RL" to it.rl.toFloat(),
                "RR" to it.rr.toFloat(),
            )
        } ?: emptyList()

    val motionStateData: List<Pair<String, Float>>
        get() = vehicleData.value?.motionState?.let {
            listOf(
                "Speed" to it.vehicleSpeedKmph.toFloat(),
                "Vibration" to it.vibrationRms.toFloat(),
            )
        } ?: emptyList()

    val environmentStateData: List<Pair<String, Float>>
        get() = vehicleData.value?.environmentState?.let {
            listOf(
                "Pressure" to it.ambientPressureKpa.toFloat(),
                "Cabin Temp" to it.cabinTempC.toFloat(),
                "Humidity" to it.cabinHumidityPct.toFloat(),
            )
        } ?: emptyList()

    val lifecycleStateData: List<Pair<String, Float>>
        get() = vehicleData.value?.lifecycleState?.let {
            listOf(
                "Engine RUL" to it.engineRulPct.toFloat(),
                "Brake RUL" to it.brakeRulPct.toFloat(),
                "Battery RUL" to it.batteryRulPct.toFloat(),
            )
        } ?: emptyList()

    val globalHealthData: List<Pair<String, Float>>
        get() = vehicleData.value?.globalHealth?.let {
            listOf(
                "Health Score" to it.vehicleHealthScore.toFloat(),
            )
        } ?: emptyList()
}
