package com.example.fog_app

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.Build
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat
import com.google.gson.GsonBuilder
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.first

class FogNodeService : Service() {

    private val serviceJob = Job()
    private val serviceScope = CoroutineScope(Dispatchers.IO + serviceJob)

    companion object {
        const val CHANNEL_ID = "FogNodeServiceChannel"
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        createNotificationChannel()
        val notification = NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("Fog Node Service")
            .setContentText("Processing vehicle data in the background")
            .build()

        startForeground(1, notification)

        Log.d("FogDataService", "Service starting.")

        serviceScope.launch {
            val buffer = TelemetryBuffer(MAX_SAMPLES)
            var nextTick = System.nanoTime()
            var lastCloud = System.nanoTime()

            while (isActive) {
                try {
                    val ip = VehicleDataRepository.esp32Ip.first()
                    val samplePeriod = VehicleDataRepository.samplePeriod.first()
                    val windowSec = VehicleDataRepository.windowSec.first()

                    val data = getDataFromESP32(ip)
                    buffer.push(data)

                    if (buffer.full()) {
                        val agg = aggregate(buffer.all(), samplePeriod)
                        val health = computeHealth(agg)

                        val gson = GsonBuilder().setPrettyPrinting().create()
                        val rawJson = gson.toJson(data)
                        val processedHealthVector = gson.toJson(health)
                        val vehicleData = gson.fromJson(rawJson, VehicleData::class.java)

                        VehicleDataRepository.updateVehicleData(vehicleData, rawJson, processedHealthVector)

                        if (health["actuation"] as Boolean) {
                            sendToESP32(ip, buildActuationPacket(agg, health))
                            sendToBackend(CLOUD_URL, buildCloudPacket(agg, health))
                            lastCloud = System.nanoTime()
                        } else if ((System.nanoTime() - lastCloud) / 1e9 >= 10) {
                            sendToBackend(CLOUD_URL, buildCloudPacket(agg, health))
                            lastCloud = System.nanoTime()
                        }
                    }

                    // Use delay instead of Thread.sleep
                    nextTick += (samplePeriod * 1e9).toLong()
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

    override fun onBind(intent: Intent?): IBinder? {
        return null
    }
    
    override fun onDestroy() {
        super.onDestroy()
        Log.d("FogDataService", "Service stopping.")
        serviceJob.cancel()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val serviceChannel = NotificationChannel(
                CHANNEL_ID,
                "Fog Node Service Channel",
                NotificationManager.IMPORTANCE_DEFAULT
            )
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(serviceChannel)
        }
    }
}
