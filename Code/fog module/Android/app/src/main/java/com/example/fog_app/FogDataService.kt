package com.example.fog_app

import android.app.Service
import android.content.Intent
import android.os.IBinder
import android.util.Log
import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.combine

class FogDataService : Service() {

    private val serviceJob = Job()
    private val serviceScope = CoroutineScope(Dispatchers.IO + serviceJob)
    private val mapper = jacksonObjectMapper()

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        Log.d("FogDataService", "Service starting.")

        serviceScope.launch {
            // Observe configuration changes
            var currentIp = VehicleDataRepository.esp32Ip.value
            var currentSamplePeriod = VehicleDataRepository.samplePeriod.value
            var currentWindowSec = VehicleDataRepository.windowSec.value
            
            var maxSamples = (currentWindowSec / currentSamplePeriod).toInt()
            var buffer = TelemetryBuffer(maxSamples)
            
            var nextTick = System.nanoTime()
            var lastCloud = System.nanoTime()

            // Coroutine to update local config values from repository
            launch {
                combine(
                    VehicleDataRepository.esp32Ip,
                    VehicleDataRepository.samplePeriod,
                    VehicleDataRepository.windowSec
                ) { ip, period, window ->
                    Triple(ip, period, window)
                }.collect { (ip, period, window) ->
                    currentIp = ip
                    currentSamplePeriod = period
                    currentWindowSec = window
                    
                    val newMax = (window / period).toInt()
                    if (newMax != maxSamples) {
                        maxSamples = newMax
                        buffer = TelemetryBuffer(maxSamples) // Reset buffer on size change
                    }
                }
            }

            while (isActive) {
                try {
                    val data = getDataFromESP32(currentIp)
                    
                    if (data != null) {
                        val rawJson = mapper.writerWithDefaultPrettyPrinter().writeValueAsString(data)
                        VehicleDataRepository.updateRawJson(rawJson)
                        
                        buffer.push(data)

                        if (buffer.full()) {
                            val agg = aggregate(buffer.all(), currentSamplePeriod)
                            val health = computeHealth(agg)

                            val healthVector = mapper.writerWithDefaultPrettyPrinter().writeValueAsString(health)
                            VehicleDataRepository.updateProcessedHealthVector(healthVector)

                            if (health["actuation"] as Boolean) {
                                sendToESP32(currentIp, buildActuationPacket(agg, health))
                                sendToBackend(CLOUD_URL, buildCloudPacket(agg, health))
                                lastCloud = System.nanoTime()
                            } else if ((System.nanoTime() - lastCloud) / 1e9 >= 1) {
                                sendToBackend(CLOUD_URL, buildCloudPacket(agg, health))
                                lastCloud = System.nanoTime()
                            }
                        }
                    }

                    nextTick += (currentSamplePeriod * 1e9).toLong()
                    val sleepNanos = nextTick - System.nanoTime()
                    if (sleepNanos > 0) {
                        delay(sleepNanos / 1_000_000)
                    }

                } catch (e: Exception) {
                    Log.e("FogDataService", "Error in background task", e)
                }
            }
        }

        return START_STICKY
    }

    override fun onDestroy() {
        super.onDestroy()
        Log.d("FogDataService", "Service stopping.")
        serviceJob.cancel()
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
