package com.example.fog_app

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow

object VehicleDataRepository {
    // Configuration
    val esp32Ip = MutableStateFlow(ESP32_IP)
    val samplePeriod = MutableStateFlow(SAMPLE_PERIOD)
    val windowSec = MutableStateFlow(WINDOW_SEC)

    // Output Data
    private val _vehicleData = MutableStateFlow<VehicleData?>(null)
    val vehicleData = _vehicleData.asStateFlow()

    private val _rawJson = MutableStateFlow("")
    val rawJson = _rawJson.asStateFlow()

    private val _processedHealthVector = MutableStateFlow("")
    val processedHealthVector = _processedHealthVector.asStateFlow()

    fun updateVehicleData(newData: VehicleData?, newJson: String, newHealthVector: String) {
        _vehicleData.value = newData
        _rawJson.value = newJson
        _processedHealthVector.value = newHealthVector
    }
}
