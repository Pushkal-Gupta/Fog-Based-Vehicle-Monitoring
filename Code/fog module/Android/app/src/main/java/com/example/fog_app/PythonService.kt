package com.example.fog_app

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
// import com.chaquo.python.Python
// import com.chaquo.python.android.AndroidPlatform

class PythonService : Service() {

    companion object {
        const val CHANNEL_ID = "PythonServiceChannel"
    }

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        val notification = NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("Python Service")
            .setContentText("Running Python script in the background")
            .build()

        startForeground(1, notification)

        // if (!Python.isStarted()) {
        //     Python.start(AndroidPlatform(this))
        // }
        // val py = Python.getInstance()
        // py.getModule("fog_node").callAttr("run")
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? {
        return null
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val serviceChannel = NotificationChannel(
                CHANNEL_ID,
                "Python Service Channel",
                NotificationManager.IMPORTANCE_DEFAULT
            )
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(serviceChannel)
        }
    }
}