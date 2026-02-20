package com.example.fog_app

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DeveloperLogsScreen(onBack: () -> Unit, viewModel: DashboardViewModel = viewModel()) {
    val vehicleData by viewModel.vehicleData.collectAsState()
    val scrollState = rememberScrollState()
    val clipboardManager = LocalClipboardManager.current

    val esp32Ip by viewModel.esp32Ip.collectAsState()
    val samplePeriod by viewModel.samplePeriod.collectAsState()
    val windowSec by viewModel.windowSec.collectAsState()

    var esp32IpInput by remember(esp32Ip) { mutableStateOf(esp32Ip) }
    var samplePeriodInput by remember(samplePeriod) { mutableStateOf(samplePeriod.toString()) }
    var windowSecInput by remember(windowSec) { mutableStateOf(windowSec.toString()) }

    Surface(modifier = Modifier.fillMaxSize(), color = Color.Black) {
        Scaffold(
            topBar = {
                TopAppBar(
                    title = { Text("Developer Logs") },
                    navigationIcon = {
                        IconButton(onClick = onBack) {
                            Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                        }
                    },
                    colors = TopAppBarDefaults.topAppBarColors(
                        containerColor = Color.Black,
                        titleContentColor = Color.White,
                        navigationIconContentColor = Color.White
                    )
                )
            },
            containerColor = Color.Black
        ) { paddingValues ->
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues)
                    .padding(16.dp)
                    .verticalScroll(scrollState)
            ) {
                // Configuration fields
                OutlinedTextField(
                    value = esp32IpInput,
                    onValueChange = { 
                        esp32IpInput = it
                        viewModel.setEsp32Ip(it)
                    },
                    label = { Text("ESP32 IP Address") },
                    modifier = Modifier.fillMaxWidth(),
                     colors = TextFieldDefaults.colors(
                    focusedTextColor = Color.White,
                    unfocusedTextColor = Color.White,
                    focusedContainerColor = Color.DarkGray,
                    unfocusedContainerColor = Color.DarkGray,
                    disabledContainerColor = Color.DarkGray,
                )
                )
                Spacer(modifier = Modifier.height(8.dp))
                OutlinedTextField(
                    value = samplePeriodInput,
                    onValueChange = { 
                        samplePeriodInput = it
                        it.toDoubleOrNull()?.let { value -> viewModel.setSamplePeriod(value) }
                    },
                    label = { Text("Sample Period (seconds)") },
                    modifier = Modifier.fillMaxWidth(),
                    colors = TextFieldDefaults.colors(
                    focusedTextColor = Color.White,
                    unfocusedTextColor = Color.White,
                    focusedContainerColor = Color.DarkGray,
                    unfocusedContainerColor = Color.DarkGray,
                    disabledContainerColor = Color.DarkGray,
                )
                )
                Spacer(modifier = Modifier.height(8.dp))
                OutlinedTextField(
                    value = windowSecInput,
                    onValueChange = { 
                        windowSecInput = it
                        it.toDoubleOrNull()?.let { value -> viewModel.setWindowSec(value) }
                     },
                    label = { Text("Window Size (seconds)") },
                    modifier = Modifier.fillMaxWidth(),
                    colors = TextFieldDefaults.colors(
                    focusedTextColor = Color.White,
                    unfocusedTextColor = Color.White,
                    focusedContainerColor = Color.DarkGray,
                    unfocusedContainerColor = Color.DarkGray,
                    disabledContainerColor = Color.DarkGray,
                )
                )
                Spacer(modifier = Modifier.height(16.dp))
                val aggregationValue = if (samplePeriod != 0.0) (windowSec / samplePeriod).toInt() else 0
                Text("Aggregation Value: $aggregationValue", color = Color.White)
                Spacer(modifier = Modifier.height(16.dp))

                // Processed Health Vector
                Text("Processed Health Vector:", style = MaterialTheme.typography.titleMedium, color = Color.White)
                Spacer(modifier = Modifier.height(8.dp))
                SelectionContainer {
                    Text(
                        text = viewModel.getProcessedHealthVector(),
                        style = MaterialTheme.typography.bodyMedium,
                        color = Color.White
                    )
                }
                Button(onClick = {
                    clipboardManager.setText(AnnotatedString(viewModel.getProcessedHealthVector()))
                }) {
                    Text("Copy")
                }
                Spacer(modifier = Modifier.height(16.dp))

                // Raw JSON from ESP32
                Text("Raw JSON from ESP32:", style = MaterialTheme.typography.titleMedium, color = Color.White)
                Spacer(modifier = Modifier.height(8.dp))
                SelectionContainer {
                    Text(
                        text = viewModel.getRawJson(),
                        style = MaterialTheme.typography.bodyMedium,
                        color = Color.White
                    )
                }
                Button(onClick = {
                    clipboardManager.setText(AnnotatedString(viewModel.getRawJson()))
                }) {
                    Text("Copy")
                }
            }
        }
    }
}
