package com.example.fog_app

import android.app.Service
import android.content.Intent
import android.os.IBinder
import android.util.Log
import kotlinx.coroutines.*

class FogDataService : Service() {

    private val serviceJob = Job()
    private val serviceScope = CoroutineScope(Dispatchers.IO + serviceJob)

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        Log.d("FogDataService", "Service starting.")

        serviceScope.launch {
            val buffer = TelemetryBuffer(MAX_SAMPLES)
            var nextTick = System.nanoTime()
            var lastCloud = System.nanoTime()

            while (isActive) {
                try {
                    // Use the dynamic IP from the repository
                    val currentIp = VehicleDataRepository.esp32Ip.value
                    val data = getDataFromESP32(currentIp)
                    buffer.push(data)

                    if (buffer.full()) {
                        val agg = aggregate(buffer.all(), SAMPLE_PERIOD)
                        val health = computeHealth(agg)

                        if (health["actuation"] as Boolean) {
                            sendToESP32(currentIp, buildActuationPacket(agg, health))
                            sendToBackend(CLOUD_URL, buildCloudPacket(agg, health))
                            lastCloud = System.nanoTime()
                        } else if ((System.nanoTime() - lastCloud) / 1e9 >= 1) {
                            sendToBackend(CLOUD_URL, buildCloudPacket(agg, health))
                            lastCloud = System.nanoTime()
                        }
                    }

                    nextTick += (SAMPLE_PERIOD * 1e9).toLong()
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
