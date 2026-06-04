package com.example.mantenimientoapp.ui.cronograma

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ChevronLeft
import androidx.compose.material.icons.filled.ChevronRight
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.example.mantenimientoapp.data.remote.dto.CronogramaFilaDto
import com.example.mantenimientoapp.ui.components.ErrorBox
import com.example.mantenimientoapp.ui.components.LoadingBox
import java.util.Calendar

@Composable
fun CronogramaScreen(
    modifier: Modifier = Modifier,
    vm: CronogramaViewModel = hiltViewModel()
) {
    val state by vm.state.collectAsState()
    var anio by remember { mutableStateOf(Calendar.getInstance().get(Calendar.YEAR)) }

    LaunchedEffect(anio) { vm.load(anio) }

    Column(modifier.fillMaxSize()) {
        // Selector de año
        Row(
            Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 8.dp),
            horizontalArrangement = Arrangement.Center,
            verticalAlignment = Alignment.CenterVertically
        ) {
            IconButton(onClick = { anio-- }) { Icon(Icons.Default.ChevronLeft, "Año anterior") }
            Text("$anio", style = MaterialTheme.typography.titleLarge, modifier = Modifier.padding(horizontal = 24.dp))
            IconButton(onClick = { anio++ }) { Icon(Icons.Default.ChevronRight, "Año siguiente") }
        }

        when {
            state.loading -> LoadingBox()
            state.error != null -> ErrorBox(state.error!!, onRetry = { vm.load(anio) })
            state.filas.isEmpty() -> {
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Text("Sin programas para $anio", color = MaterialTheme.colorScheme.outline)
                }
            }
            else -> CronogramaTable(state.filas)
        }
    }
}

private val MESES = listOf("Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic")

@Composable
private fun CronogramaTable(filas: List<CronogramaFilaDto>) {
    LazyColumn(contentPadding = PaddingValues(bottom = 16.dp)) {
        // Encabezado
        item {
            Row(Modifier.fillMaxWidth().background(MaterialTheme.colorScheme.surfaceVariant)) {
                Text(
                    "Programa",
                    Modifier.width(160.dp).padding(6.dp),
                    style = MaterialTheme.typography.labelSmall,
                    fontWeight = androidx.compose.ui.text.font.FontWeight.Bold
                )
                MESES.forEach { mes ->
                    Text(
                        mes,
                        Modifier.weight(1f).padding(4.dp),
                        style = MaterialTheme.typography.labelSmall,
                        textAlign = TextAlign.Center,
                        fontWeight = androidx.compose.ui.text.font.FontWeight.Bold
                    )
                }
            }
            HorizontalDivider()
        }

        items(filas) { fila ->
            Row(
                Modifier.fillMaxWidth().padding(vertical = 2.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    fila.etiqueta,
                    Modifier.width(160.dp).padding(horizontal = 6.dp, vertical = 4.dp),
                    style = MaterialTheme.typography.bodySmall,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis
                )
                (1..12).forEach { mes ->
                    val estado = fila.meses[mes.toString()]
                    Box(
                        Modifier.weight(1f).padding(2.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        if (estado != null) {
                            Surface(
                                shape = MaterialTheme.shapes.small,
                                color = estadoColor(estado).copy(alpha = 0.85f),
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Text(
                                    estadoLabel(estado),
                                    modifier = Modifier.padding(2.dp),
                                    fontSize = 8.sp,
                                    textAlign = TextAlign.Center,
                                    color = Color.White
                                )
                            }
                        }
                    }
                }
            }
            HorizontalDivider(thickness = 0.5.dp)
        }
    }
}

private fun estadoColor(estado: String) = when (estado) {
    "planned" -> Color(0xFF3B82F6)
    "activa" -> Color(0xFFF59E0B)
    "completada" -> Color(0xFF10B981)
    else -> Color.Gray
}

private fun estadoLabel(estado: String) = when (estado) {
    "planned" -> "Plan"
    "activa" -> "Activa"
    "completada" -> "OK"
    else -> estado
}
