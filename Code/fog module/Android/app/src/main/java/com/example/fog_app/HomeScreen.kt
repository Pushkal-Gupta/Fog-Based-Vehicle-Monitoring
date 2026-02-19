package com.example.fog_app

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

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
        "Thermal State", "Powertrain State", "Electrical State",
        "Braking State", "Tires State", "Motion State",
        "Environment State", "Lifecycle State", "Global Health"
    )

    LazyVerticalGrid(
        columns = GridCells.Fixed(2),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
        horizontalArrangement = Arrangement.spacedBy(16.dp),
        modifier = Modifier.fillMaxSize()
    ) {
        items(dataCategories) { category ->
            CategoryTile(category = category, onClick = { onTileClick(category) })
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
fun CategoryTile(category: String, onClick: () -> Unit) {
    Card(
        modifier = Modifier
            .aspectRatio(1f)
            .clickable(onClick = onClick),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
    ) {
        Box(modifier = Modifier.fillMaxSize().padding(8.dp), contentAlignment = Alignment.Center) {
            Text(text = category, style = MaterialTheme.typography.titleMedium)
        }
    }
}
