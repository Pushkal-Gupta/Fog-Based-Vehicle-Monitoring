package com.example.fog_app

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.itemsIndexed
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.example.fog_app.ui.theme.*

data class DashboardCategory(val name: String, val icon: ImageVector)

@Composable
fun HomeScreen(userType: UserType, onTileClick: (String) -> Unit, onLogsClick: () -> Unit) {
    when (userType) {
        UserType.USER -> UserHomeScreen(onTileClick = onTileClick)
        UserType.DEVELOPER -> DeveloperHomeScreen(onLogsClick = onLogsClick)
    }
}

@Composable
fun UserHomeScreen(onTileClick: (String) -> Unit) {
    val dataCategories = listOf(
        DashboardCategory("Thermal State", Icons.Default.Thermostat),
        DashboardCategory("Powertrain State", Icons.Default.Settings),
        DashboardCategory("Electrical State", Icons.Default.ElectricalServices),
        DashboardCategory("Braking State", Icons.Default.DiscFull),
        DashboardCategory("Tires State", Icons.Default.DonutLarge),
        DashboardCategory("Motion State", Icons.Default.DirectionsCar),
        DashboardCategory("Environment State", Icons.Default.WbSunny),
        DashboardCategory("Lifecycle State", Icons.Default.Autorenew),
        DashboardCategory("Global Health", Icons.Default.Favorite)
    )

    val tileColors = listOf(
        Color(0xFFF44336), Color(0xFFE91E63), Color(0xFF9C27B0), Color(0xFF673AB7),
        Color(0xFF3F51B5), Color(0xFF2196F3), Color(0xFF03A9F4), Color(0xFF00BCD4), Color(0xFF009688)
    )

    Surface(color = Color.Black, modifier = Modifier.fillMaxSize()) {
        LazyVerticalGrid(
            columns = GridCells.Fixed(2),
            contentPadding = PaddingValues(start = 16.dp, top = 48.dp, end = 16.dp, bottom = 16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
            horizontalArrangement = Arrangement.spacedBy(16.dp),
            modifier = Modifier.fillMaxSize()
        ) {
            itemsIndexed(dataCategories) { index, category ->
                CategoryTile(
                    category = category.name,
                    icon = category.icon,
                    color = tileColors[index % tileColors.size],
                    onClick = { onTileClick(category.name) }
                )
            }
        }
    }
}

@Composable
fun DeveloperHomeScreen(onLogsClick: () -> Unit) {
    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Button(onClick = onLogsClick) {
            Text("View Logs")
        }
    }
}

@Composable
fun CategoryTile(category: String, icon: ImageVector, color: Color, onClick: () -> Unit) {
    Card(
        modifier = Modifier
            .aspectRatio(1f)
            .clickable(onClick = onClick),
        elevation = CardDefaults.cardElevation(defaultElevation = 8.dp),
        colors = CardDefaults.cardColors(containerColor = color)
    ) {
        Column(
            modifier = Modifier.fillMaxSize().padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Icon(imageVector = icon, contentDescription = category, tint = Color.White, modifier = Modifier.size(48.dp))
            Spacer(modifier = Modifier.height(16.dp))
            Text(text = category, style = MaterialTheme.typography.titleMedium, color = Color.White, textAlign = TextAlign.Center)
        }
    }
}
