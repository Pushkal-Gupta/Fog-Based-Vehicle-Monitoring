package com.example.fog_app

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.ui.Modifier
import com.example.fog_app.ui.theme.Fog_AppTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        val serviceIntent = Intent(this, PythonService::class.java)
        startService(serviceIntent)

        enableEdgeToEdge()
        setContent {
            Fog_AppTheme {
                Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
                    DashboardScreen(
                        modifier = Modifier.padding(innerPadding)
                    )
                }
            }
        }
    }
}
