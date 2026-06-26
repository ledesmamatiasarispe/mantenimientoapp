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
    onRepuestos: () -> Unit,
    onConsolidado: () -> Unit,
    onProveedores: () -> Unit,
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
        verticalArrangement = Arrangement.spacedBy(6.dp)
    ) {
        // ── Monitoreo ─────────────────────────────────────────────────────────
        GrupoHeader("🔔 Monitoreo")
        AdminCard("Dashboard", "Resumen general del sistema", Icons.Default.Dashboard, onDashboard)
        AdminCard("Alertas", "Stock bajo, órdenes sin asignar, mantenimientos vencidos", Icons.Default.Notifications, onAlertas)

        Spacer(Modifier.height(8.dp))

        // ── Gestión ───────────────────────────────────────────────────────────
        GrupoHeader("⚙️ Gestión")
        AdminCard("Equipos", "Máquinas, programas, repuestos e historial", Icons.Default.Build, onEquipos)
        AdminCard("Repuestos", "Catálogo de repuestos", Icons.Default.Inventory, onRepuestos)
        AdminCard("Stock consolidado", "Mínimos por equipo y alertas", Icons.Default.BarChart, onConsolidado)
        AdminCard("Proveedores", "Empresas proveedoras de repuestos", Icons.Default.Business, onProveedores)
        AdminCard("Técnicos", "Usuarios del sistema", Icons.Default.People, onTecnicos)

        Spacer(Modifier.height(8.dp))

        // ── Herramientas ──────────────────────────────────────────────────────
        GrupoHeader("🔧 Herramientas")
        AdminCard("Generar órdenes", "Crear órdenes preventivas para un mes", Icons.Default.PlaylistAdd, onGenerarOrdenes)
        AdminCard("Electricidad / EDESUR", "Medidores, facturas y gráficos", Icons.Default.ElectricBolt, onElectricidad)
        AdminCard("Base de datos", "Exportar o importar la base de datos", Icons.Default.Storage, onExportImportDb)

        Spacer(Modifier.height(16.dp))
    }
}

@Composable
private fun GrupoHeader(titulo: String) {
    Text(
        titulo,
        style = MaterialTheme.typography.labelLarge,
        color = MaterialTheme.colorScheme.outline,
        modifier = Modifier.padding(top = 4.dp, bottom = 2.dp)
    )
}

@Composable
private fun AdminCard(title: String, subtitle: String, icon: ImageVector, onClick: () -> Unit) {
    Card(onClick = onClick, modifier = Modifier.fillMaxWidth()) {
        Row(Modifier.padding(14.dp), horizontalArrangement = Arrangement.spacedBy(14.dp)) {
            Icon(icon, null, Modifier.size(26.dp), tint = MaterialTheme.colorScheme.primary)
            Column {
                Text(title, style = MaterialTheme.typography.titleSmall)
                Text(subtitle, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
            }
        }
    }
}
