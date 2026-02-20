package com.example.fog_app

import android.content.Intent
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.runtime.*
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.example.fog_app.ui.theme.Fog_AppTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        Intent(this, FogNodeService::class.java).also { intent ->
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                startForegroundService(intent)
            } else {
                startService(intent)
            }
        }

        setContent {
            Fog_AppTheme {
                val navController = rememberNavController()
                NavHost(navController = navController, startDestination = "login") {
                    composable("login") {
                        LoginScreen(onLogin = {
                            if (it == UserType.DEVELOPER) {
                                navController.navigate("logs")
                            } else {
                                navController.navigate("home/${it.name}")
                            }
                        })
                    }
                    composable(
                        "home/{userType}",
                        arguments = listOf(navArgument("userType") { type = NavType.StringType })
                    ) { backStackEntry ->
                        val userType = UserType.valueOf(backStackEntry.arguments?.getString("userType") ?: "USER")
                        HomeScreen(
                            userType = userType,
                            onTileClick = { category -> navController.navigate("chart/$category") },
                            onLogsClick = { navController.navigate("logs") }
                        )
                    }
                    composable(
                        "chart/{category}",
                        arguments = listOf(navArgument("category") { type = NavType.StringType })
                    ) { backStackEntry ->
                        val category = backStackEntry.arguments?.getString("category") ?: ""
                        ChartScreen(category = category, onBack = { navController.popBackStack() })
                    }
                    composable("logs") {
                        DeveloperLogsScreen(onBack = { navController.popBackStack() })
                    }
                }
            }
        }
    }
}
