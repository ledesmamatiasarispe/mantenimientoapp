package com.example.mantenimientoapp.ui.admin

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.dp

@Composable
fun AdminScreen(
    modifier: Modifier = Modifier,
    onDashboard: () -> Unit,
    onAlertas: () -> Unit,
    onEquipos: () -> Unit,
    onProgramas: () -> Unit,
    onRepuestos: () -> Unit,
    onTecnicos: () -> Unit,
    onGenerarOrdenes: () -> Unit,
    onElectricidad: () -> Unit,
    onExportImportDb: () -> Unit
) {
    Column(
        modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        Text("Panel de administración", style = MaterialTheme.typography.titleLarge)
        Spacer(Modifier.height(4.dp))

        AdminCard("Dashboard", "Resumen general del sistema", Icons.Default.Dashboard, onDashboard)
        AdminCard("Alertas", "Stock bajo, órdenes sin asignar, mantenimientos vencidos", Icons.Default.Notifications, onAlertas)
        HorizontalDivider()
        AdminCard("Equipos", "Gestionar equipos y tipos", Icons.Default.Build, onEquipos)
        AdminCard("Programas de mantenimiento", "Programas preventivos y sus pasos", Icons.Default.EventNote, onProgramas)
        AdminCard("Repuestos", "Stock e inventario", Icons.Default.Inventory, onRepuestos)
        AdminCard("Técnicos", "Usuarios del sistema", Icons.Default.People, onTecnicos)
        HorizontalDivider()
        AdminCard("Generar órdenes", "Crear órdenes preventivas para un mes", Icons.Default.PlaylistAdd, onGenerarOrdenes)
        AdminCard("Electricidad / EDESUR", "Medidores, facturas y gráficos", Icons.Default.ElectricBolt, onElectricidad)
        AdminCard("Base de datos", "Exportar o importar la base de datos", Icons.Default.Storage, onExportImportDb)
    }
}

@Composable
private fun AdminCard(title: String, subtitle: String, icon: ImageVector, onClick: () -> Unit) {
    Card(onClick = onClick, modifier = Modifier.fillMaxWidth()) {
        Row(Modifier.padding(14.dp), horizontalArrangement = Arrangement.spacedBy(14.dp)) {
            Icon(icon, null, Modifier.size(28.dp), tint = MaterialTheme.colorScheme.primary)
            Column {
                Text(title, style = MaterialTheme.typography.titleSmall)
                Text(subtitle, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
            }
        }
    }
}
