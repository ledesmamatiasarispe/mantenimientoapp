package com.example.mantenimientoapp.ui.ordenes

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.example.mantenimientoapp.data.remote.dto.EquipoCardDto
import com.example.mantenimientoapp.data.remote.dto.OrdenCardDto
import com.example.mantenimientoapp.ui.components.ErrorBox
import com.example.mantenimientoapp.ui.components.EstadoChip
import com.example.mantenimientoapp.ui.components.LoadingBox
import com.example.mantenimientoapp.ui.components.TipoChip

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun OrdenesScreen(
    onOrdenClick: (Int) -> Unit,
    modifier: Modifier = Modifier,
    vm: OrdenesViewModel = hiltViewModel()
) {
    val state by vm.state.collectAsState()
    val equipos by vm.equipos.collectAsState()
    var showNuevaOrden by remember { mutableStateOf(false) }

    val tabs = listOf("Pendientes", "Mis órdenes", "Todas", "Completadas")
    var selectedTab by remember { mutableStateOf(0) }

    val listaActual = when (selectedTab) {
        0 -> state.pendientes
        1 -> state.mias
        2 -> state.todas
        else -> state.completadas
    }

    Scaffold(
        floatingActionButton = {
            FloatingActionButton(onClick = { showNuevaOrden = true }) {
                Icon(Icons.Default.Add, "Nueva orden")
            }
        }
    ) { padding ->
        Column(modifier.padding(padding)) {
            // Tabs
            ScrollableTabRow(selectedTabIndex = selectedTab) {
                tabs.forEachIndexed { i, label ->
                    Tab(selected = selectedTab == i, onClick = { selectedTab = i }) {
                        Text(label, modifier = Modifier.padding(vertical = 12.dp, horizontal = 8.dp))
                    }
                }
            }

            when {
                state.loading -> LoadingBox()
                state.error != null -> ErrorBox(state.error!!, onRetry = { vm.loadAll() })
                listaActual.isEmpty() -> {
                    Box(
                        Modifier.fillMaxSize(),
                        contentAlignment = androidx.compose.ui.Alignment.Center
                    ) {
                        Text("No hay órdenes", color = MaterialTheme.colorScheme.outline)
                    }
                }
                else -> {
                    LazyColumn(contentPadding = PaddingValues(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        item {
                            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.End) {
                                IconButton(onClick = { vm.loadAll() }) {
                                    Icon(Icons.Default.Refresh, "Actualizar")
                                }
                            }
                        }
                        items(listaActual, key = { it.id }) { orden ->
                            OrdenCard(orden = orden, onClick = { onOrdenClick(orden.id) })
                        }
                    }
                }
            }
        }
    }

    if (showNuevaOrden) {
        NuevaOrdenDialog(
            equipos = equipos,
            onDismiss = { showNuevaOrden = false },
            onConfirm = { equipoId, tipo, descripcion, obs ->
                vm.crearOrden(equipoId, tipo, descripcion, obs) { ok, _ ->
                    if (ok) showNuevaOrden = false
                }
            }
        )
    }
}

@Composable
private fun OrdenCard(orden: OrdenCardDto, onClick: () -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth().clickable(onClick = onClick),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text("#${orden.id}", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.outline)
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    TipoChip(orden.tipo)
                    EstadoChip(orden.estado)
                }
            }
            Text(orden.equipoNombre, style = MaterialTheme.typography.titleMedium)
            if (orden.equipoUbicacion.isNotBlank()) {
                Text(orden.equipoUbicacion, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
            }
            if (orden.tecnicoNombre.isNotBlank()) {
                Text("Técnico: ${orden.tecnicoNombre}", style = MaterialTheme.typography.bodySmall)
            }
            Text(orden.fechaApertura.take(10), style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun NuevaOrdenDialog(
    equipos: List<EquipoCardDto>,
    onDismiss: () -> Unit,
    onConfirm: (Int, String, String, String) -> Unit
) {
    var equipoId by remember { mutableStateOf<Int?>(null) }
    var tipo by remember { mutableStateOf("CORRECTIVO") }
    var descripcion by remember { mutableStateOf("") }
    var observaciones by remember { mutableStateOf("") }
    var expandedEquipo by remember { mutableStateOf(false) }
    var expandedTipo by remember { mutableStateOf(false) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Nueva orden de trabajo") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                // Equipo
                ExposedDropdownMenuBox(expanded = expandedEquipo, onExpandedChange = { expandedEquipo = it }) {
                    OutlinedTextField(
                        value = equipos.find { it.id == equipoId }?.nombre ?: "Seleccionar equipo",
                        onValueChange = {},
                        readOnly = true,
                        label = { Text("Equipo") },
                        trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expandedEquipo) },
                        modifier = Modifier.menuAnchor().fillMaxWidth()
                    )
                    ExposedDropdownMenu(expanded = expandedEquipo, onDismissRequest = { expandedEquipo = false }) {
                        equipos.forEach { eq ->
                            DropdownMenuItem(
                                text = { Text(eq.nombre) },
                                onClick = { equipoId = eq.id; expandedEquipo = false }
                            )
                        }
                    }
                }

                // Tipo
                ExposedDropdownMenuBox(expanded = expandedTipo, onExpandedChange = { expandedTipo = it }) {
                    OutlinedTextField(
                        value = tipo,
                        onValueChange = {},
                        readOnly = true,
                        label = { Text("Tipo") },
                        trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expandedTipo) },
                        modifier = Modifier.menuAnchor().fillMaxWidth()
                    )
                    ExposedDropdownMenu(expanded = expandedTipo, onDismissRequest = { expandedTipo = false }) {
                        listOf("PREVENTIVO", "CORRECTIVO", "MEJORA").forEach { t ->
                            DropdownMenuItem(text = { Text(t) }, onClick = { tipo = t; expandedTipo = false })
                        }
                    }
                }

                OutlinedTextField(
                    value = descripcion,
                    onValueChange = { descripcion = it },
                    label = { Text("Descripción") },
                    modifier = Modifier.fillMaxWidth()
                )
                OutlinedTextField(
                    value = observaciones,
                    onValueChange = { observaciones = it },
                    label = { Text("Observaciones") },
                    modifier = Modifier.fillMaxWidth()
                )
            }
        },
        confirmButton = {
            TextButton(
                onClick = { equipoId?.let { onConfirm(it, tipo, descripcion, observaciones) } },
                enabled = equipoId != null
            ) { Text("Crear") }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancelar") } }
    )
}
