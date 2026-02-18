package com.example.fog_app

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel

@Composable
fun DashboardScreen(viewModel: DashboardViewModel = viewModel()) {
    val vehicleData by viewModel.vehicleData.collectAsState()

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        item {
            vehicleData?.let { data ->
                VehicleDataCard(title = "Meta", content = data.meta.toString())
                VehicleDataCard(title = "Thermal State", content = data.thermalState.toString())
                VehicleDataCard(title = "Powertrain State", content = data.powertrainState.toString())
                VehicleDataCard(title = "Electrical State", content = data.electricalState.toString())
                VehicleDataCard(title = "Braking State", content = data.brakingState.toString())
                VehicleDataCard(title = "Tires State", content = data.tiresState.toString())
                VehicleDataCard(title = "Motion State", content = data.motionState.toString())
                VehicleDataCard(title = "Environment State", content = data.environmentState.toString())
                VehicleDataCard(title = "Lifecycle State", content = data.lifecycleState.toString())
                VehicleDataCard(title = "Global Health", content = data.globalHealth.toString())
                VehicleDataCard(title = "Fog Decision", content = data.fogDecision.toString())
                VehicleDataCard(title = "Safety Flags", content = data.safetyFlags.toString())
                VehicleDataCard(title = "Trigger Source Data", content = data.triggerSourceData.toString())
                VehicleDataCard(title = "Actuation State", content = data.actuationState.toString())
            }
        }
    }
}

@Composable
fun VehicleDataCard(title: String, content: String) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(text = title, style = androidx.compose.material3.MaterialTheme.typography.titleMedium)
            Spacer(modifier = Modifier.height(8.dp))
            Text(text = content)
        }
    }
}
