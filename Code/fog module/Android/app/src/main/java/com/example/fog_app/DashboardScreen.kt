package com.example.fog_app

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.viewmodel.compose.viewModel
import com.github.mikephil.charting.charts.LineChart
import com.github.mikephil.charting.components.XAxis
import com.github.mikephil.charting.data.Entry
import com.github.mikephil.charting.data.LineData
import com.github.mikephil.charting.data.LineDataSet
import com.github.mikephil.charting.formatter.IndexAxisValueFormatter

// This screen is now a placeholder for the chart component.
@Composable
fun DashboardScreen(modifier: Modifier = Modifier, viewModel: DashboardViewModel = viewModel()) {
    val vehicleData by viewModel.vehicleData.collectAsState()

    Column(modifier = modifier.fillMaxSize().padding(16.dp)) {
        Text("Vehicle Data", style = MaterialTheme.typography.headlineMedium)

        vehicleData?.let { data ->
            val thermalData = viewModel.thermalStateData
            if (thermalData.isNotEmpty()) {
                VehicleDataChart(
                    data = thermalData,
                    title = "Thermal State",
                    modifier = Modifier.fillMaxSize() // Use fillMaxSize to take up available space
                )
            }
        }
    }
}

@Composable
fun VehicleDataChart(data: List<Pair<String, Float>>, title: String, modifier: Modifier = Modifier) {
    val onBackgroundColor = MaterialTheme.colorScheme.onBackground
    val primaryColor = MaterialTheme.colorScheme.primary
    val surfaceColor = MaterialTheme.colorScheme.surface

    AndroidView(
        modifier = modifier,
        factory = { context -> LineChart(context) },
        update = { chart ->
            val onBackgroundColorArgb = onBackgroundColor.toArgb()
            val primaryColorArgb = primaryColor.toArgb()
            val surfaceColorArgb = surfaceColor.toArgb()

            // General Chart Styling
            chart.setBackgroundColor(surfaceColorArgb)
            chart.description.isEnabled = false
            chart.legend.textColor = onBackgroundColorArgb
            chart.setExtraOffsets(16f, 16f, 16f, 16f)

            // X-Axis Styling
            val xAxis = chart.xAxis
            xAxis.textColor = onBackgroundColorArgb
            xAxis.position = XAxis.XAxisPosition.BOTTOM
            xAxis.granularity = 1f
            xAxis.valueFormatter = IndexAxisValueFormatter(data.map { it.first })
            xAxis.setDrawGridLines(false)

            // Y-Axis Styling
            val leftAxis = chart.axisLeft
            leftAxis.textColor = onBackgroundColorArgb
            leftAxis.setDrawGridLines(true)
            chart.axisRight.isEnabled = false

            // Data Set
            val entries = data.mapIndexed { index, pair ->
                Entry(index.toFloat(), pair.second)
            }
            val dataSet = LineDataSet(entries, title).apply {
                color = primaryColorArgb
                valueTextColor = onBackgroundColorArgb
                setCircleColor(primaryColorArgb)
                circleHoleColor = primaryColorArgb
                valueTextSize = 10f
                mode = LineDataSet.Mode.CUBIC_BEZIER
                cubicIntensity = 0.2f
                setDrawFilled(true)
                fillColor = primaryColorArgb
                fillAlpha = 100
                setDrawCircles(true)
            }

            chart.data = LineData(dataSet)
            chart.notifyDataSetChanged()
            chart.invalidate()
        }
    )
}
