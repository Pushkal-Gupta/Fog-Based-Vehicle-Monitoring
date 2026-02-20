package com.example.fog_app

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.viewmodel.compose.viewModel
import com.github.mikephil.charting.charts.LineChart
import com.github.mikephil.charting.components.XAxis
import com.github.mikephil.charting.data.Entry
import com.github.mikephil.charting.data.LineData
import com.github.mikephil.charting.data.LineDataSet
import com.github.mikephil.charting.formatter.IndexAxisValueFormatter

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChartScreen(category: String, onBack: () -> Unit, viewModel: DashboardViewModel = viewModel()) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(category) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface
                )
            )
        },
        containerColor = Color.Black
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            val data = viewModel.getDataForCategory(category)

            if (data.isNotEmpty()) {
                VehicleDataChart(
                    data = data,
                    title = category,
                    modifier = Modifier.fillMaxSize()
                )
            }
        }
    }
}

@Composable
fun VehicleDataChart(data: List<Pair<String, Float>>, title: String, modifier: Modifier = Modifier) {
    val onBackgroundColor = Color.White
    val primaryColor = MaterialTheme.colorScheme.primary

    AndroidView(
        modifier = modifier,
        factory = { context -> LineChart(context) },
        update = { chart ->
            val onBackgroundColorArgb = onBackgroundColor.toArgb()
            val primaryColorArgb = primaryColor.toArgb()
            val surfaceColorArgb = Color.Black.toArgb()

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
