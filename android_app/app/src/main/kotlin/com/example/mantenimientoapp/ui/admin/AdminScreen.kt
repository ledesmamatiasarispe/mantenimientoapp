package com.example.mantenimientoapp.ui.admin

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun AdminScreen(
    modifier: Modifier = Modifier,
    onEquipos: () -> Unit,
    onProgramas: () -> Unit,
    onRepuestos: () -> Unit,
    onTecnicos: () -> Unit
) {
    Column(
        modifier.fillMaxSize().padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Text("Panel de administración", style = MaterialTheme.typography.titleLarge)
        Spacer(Modifier.height(8.dp))

        AdminCard("Equipos", "Gestionar equipos y tipos de equipo", Icons.Default.Build, onEquipos)
        AdminCard("Programas de mantenimiento", "Gestionar programas preventivos y sus pasos", Icons.Default.EventNote, onProgramas)
        AdminCard("Repuestos", "Gestionar stock de repuestos", Icons.Default.Inventory, onRepuestos)
        AdminCard("Técnicos", "Gestionar usuarios técnicos", Icons.Default.People, onTecnicos)
    }
}

@Composable
private fun AdminCard(title: String, subtitle: String, icon: androidx.compose.ui.graphics.vector.ImageVector, onClick: () -> Unit) {
    Card(
        onClick = onClick,
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(Modifier.padding(16.dp), horizontalArrangement = Arrangement.spacedBy(16.dp)) {
            Icon(icon, contentDescription = null, modifier = Modifier.size(32.dp), tint = MaterialTheme.colorScheme.primary)
            Column {
                Text(title, style = MaterialTheme.typography.titleMedium)
                Text(subtitle, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
            }
        }
    }
}
