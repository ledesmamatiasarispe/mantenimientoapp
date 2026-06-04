package com.example.mantenimientoapp.ui.ordenes

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import coil.compose.AsyncImage
import com.example.mantenimientoapp.data.remote.dto.*
import com.example.mantenimientoapp.ui.components.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun OrdenDetailScreen(
    ordenId: Int,
    onBack: () -> Unit,
    vm: OrdenDetailViewModel = hiltViewModel()
) {
    val state by vm.state.collectAsState()
    val repuestos by vm.repuestos.collectAsState()
    val tecnicoId by vm.tecnicoId.collectAsState(initial = 0)

    var showCompletarDialog by remember { mutableStateOf(false) }
    var showObservacionDialog by remember { mutableStateOf(false) }
    var showRepuestoDialog by remember { mutableStateOf(false) }
    var showConfirmEliminarFoto by remember { mutableStateOf<Int?>(null) }

    LaunchedEffect(ordenId) { vm.load(ordenId) }

    LaunchedEffect(state.actionSuccess) {
        if (!state.actionSuccess.isNullOrBlank()) {
            kotlinx.coroutines.delay(2000)
            vm.clearMessages()
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Orden #$ordenId") },
                navigationIcon = {
                    IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, "Volver") }
                },
                actions = {
                    if (state.actionLoading) CircularProgressIndicator(Modifier.size(20.dp).padding(end = 8.dp), strokeWidth = 2.dp)
                }
            )
        }
    ) { padding ->
        when {
            state.loading -> LoadingBox()
            state.error != null -> ErrorBox(state.error!!, onRetry = { vm.load(ordenId) })
            state.orden != null -> {
                val orden = state.orden!!
                val esMio = orden.tecnicoId == tecnicoId || orden.colaboradores.any { it.id == tecnicoId }
                val puedeCambiar = orden.estado != "COMPLETADA" && orden.estado != "CANCELADA"

                LazyColumn(
                    modifier = Modifier.padding(padding),
                    contentPadding = PaddingValues(16.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    // Mensajes
                    if (!state.actionError.isNullOrBlank()) {
                        item {
                            Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer)) {
                                Text(state.actionError!!, Modifier.padding(12.dp), color = MaterialTheme.colorScheme.onErrorContainer)
                            }
                        }
                    }
                    if (!state.actionSuccess.isNullOrBlank()) {
                        item {
                            Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)) {
                                Text(state.actionSuccess!!, Modifier.padding(12.dp))
                            }
                        }
                    }

                    // Encabezado
                    item {
                        Card {
                            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                    TipoChip(orden.tipo)
                                    EstadoChip(orden.estado)
                                }
                                Text(orden.equipoNombre, style = MaterialTheme.typography.headlineSmall)
                                Text("${orden.equipoTipoNombre} · ${orden.equipoMarca} ${orden.equipoModelo}", style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.outline)
                                if (orden.equipoUbicacion.isNotBlank()) Text("📍 ${orden.equipoUbicacion}", style = MaterialTheme.typography.bodySmall)
                                if (orden.descripcion.isNotBlank()) Text(orden.descripcion, style = MaterialTheme.typography.bodyMedium)
                                HorizontalDivider()
                                Text("Apertura: ${orden.fechaApertura.take(10)}", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
                                if (orden.fechaCierre.isNotBlank()) Text("Cierre: ${orden.fechaCierre.take(10)}", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
                                if (orden.tecnicoNombre.isNotBlank()) Text("Técnico: ${orden.tecnicoNombre}", style = MaterialTheme.typography.bodySmall)
                            }
                        }
                    }

                    // Acciones
                    if (puedeCambiar) {
                        item {
                            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                if (!esMio) {
                                    Button(onClick = { vm.aceptar() }, modifier = Modifier.weight(1f)) {
                                        Icon(Icons.Default.PersonAdd, null, Modifier.size(16.dp))
                                        Spacer(Modifier.width(4.dp))
                                        Text("Aceptar")
                                    }
                                } else {
                                    OutlinedButton(onClick = { vm.cancelarAceptacion() }, modifier = Modifier.weight(1f)) {
                                        Text("Salir")
                                    }
                                }
                                Button(
                                    onClick = { showCompletarDialog = true },
                                    colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.tertiary),
                                    modifier = Modifier.weight(1f)
                                ) {
                                    Icon(Icons.Default.CheckCircle, null, Modifier.size(16.dp))
                                    Spacer(Modifier.width(4.dp))
                                    Text("Completar")
                                }
                            }
                        }
                    }

                    // Colaboradores
                    if (orden.colaboradores.isNotEmpty()) {
                        item { SectionHeader("Colaboradores") }
                        items(orden.colaboradores) { col ->
                            Text("• ${col.nombre} ${col.apellido}", style = MaterialTheme.typography.bodyMedium, modifier = Modifier.padding(start = 8.dp))
                        }
                    }

                    // Programas y pasos
                    if (orden.programas.isNotEmpty()) {
                        item { SectionHeader("Programas de mantenimiento") }
                        orden.programas.forEach { prog ->
                            item {
                                Card(modifier = Modifier.fillMaxWidth()) {
                                    Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                                        Text(prog.descripcion, style = MaterialTheme.typography.titleSmall)
                                        Text("Cada ${prog.frecuenciaMeses} meses · Próxima: ${prog.proximaEjecucion.take(10)}", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
                                        if (prog.pasos.isNotEmpty()) {
                                            HorizontalDivider()
                                            prog.pasos.forEach { paso ->
                                                Row(
                                                    verticalAlignment = Alignment.CenterVertically,
                                                    modifier = Modifier.padding(vertical = 2.dp)
                                                ) {
                                                    Checkbox(
                                                        checked = paso.completado,
                                                        onCheckedChange = { if (puedeCambiar) vm.togglePaso(paso.id) },
                                                        enabled = puedeCambiar
                                                    )
                                                    Column(Modifier.weight(1f)) {
                                                        Text(paso.descripcion, style = MaterialTheme.typography.bodySmall)
                                                        if (paso.observaciones.isNotBlank()) Text(paso.observaciones, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }

                    // Repuestos
                    item {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            SectionHeader("Repuestos utilizados")
                            Spacer(Modifier.weight(1f))
                            if (puedeCambiar) {
                                IconButton(onClick = { showRepuestoDialog = true }) {
                                    Icon(Icons.Default.Add, "Agregar repuesto", Modifier.size(20.dp))
                                }
                            }
                        }
                    }
                    if (orden.repuestos.isEmpty()) {
                        item { Text("Sin repuestos registrados", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline, modifier = Modifier.padding(start = 8.dp)) }
                    } else {
                        items(orden.repuestos) { rep ->
                            Row(Modifier.fillMaxWidth().padding(vertical = 4.dp), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                                Column(Modifier.weight(1f)) {
                                    Text(rep.descripcion, style = MaterialTheme.typography.bodyMedium)
                                    Text("x${rep.cantidad} · $${rep.costoUnitario}/u", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
                                }
                                if (puedeCambiar) {
                                    IconButton(onClick = { vm.quitarRepuesto(rep.id) }) {
                                        Icon(Icons.Default.Delete, "Quitar", Modifier.size(18.dp), tint = MaterialTheme.colorScheme.error)
                                    }
                                }
                            }
                            HorizontalDivider()
                        }
                    }

                    // Observaciones
                    item {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            SectionHeader("Observaciones")
                            Spacer(Modifier.weight(1f))
                            if (puedeCambiar) {
                                IconButton(onClick = { showObservacionDialog = true }) {
                                    Icon(Icons.Default.Add, "Agregar nota", Modifier.size(20.dp))
                                }
                            }
                        }
                    }
                    if (orden.observaciones.isNotBlank()) {
                        item {
                            Card(modifier = Modifier.fillMaxWidth()) {
                                Text(orden.observaciones, Modifier.padding(12.dp), style = MaterialTheme.typography.bodySmall)
                            }
                        }
                    }

                    // Fotos
                    if (orden.fotos.isNotEmpty()) {
                        item { SectionHeader("Fotos") }
                        item {
                            androidx.compose.foundation.lazy.LazyRow(
                                horizontalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                items(orden.fotos) { foto ->
                                    Box {
                                        AsyncImage(
                                            model = vm.getFotoUrl(orden.id, foto.id),
                                            contentDescription = foto.nombre,
                                            modifier = Modifier.size(120.dp),
                                            contentScale = ContentScale.Crop
                                        )
                                        if (puedeCambiar) {
                                            IconButton(
                                                onClick = { showConfirmEliminarFoto = foto.id },
                                                modifier = Modifier.align(Alignment.TopEnd).size(24.dp)
                                            ) {
                                                Icon(Icons.Default.Close, "Eliminar foto", Modifier.size(16.dp), tint = MaterialTheme.colorScheme.error)
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }

                    item { Spacer(Modifier.height(32.dp)) }
                }
            }
        }
    }

    // Diálogos
    if (showCompletarDialog) {
        var obs by remember { mutableStateOf("") }
        AlertDialog(
            onDismissRequest = { showCompletarDialog = false },
            title = { Text("Completar orden") },
            text = {
                OutlinedTextField(value = obs, onValueChange = { obs = it }, label = { Text("Observaciones finales") }, modifier = Modifier.fillMaxWidth())
            },
            confirmButton = {
                TextButton(onClick = { vm.completar(obs); showCompletarDialog = false }) { Text("Confirmar") }
            },
            dismissButton = { TextButton(onClick = { showCompletarDialog = false }) { Text("Cancelar") } }
        )
    }

    if (showObservacionDialog) {
        var texto by remember { mutableStateOf("") }
        AlertDialog(
            onDismissRequest = { showObservacionDialog = false },
            title = { Text("Agregar observación") },
            text = {
                OutlinedTextField(value = texto, onValueChange = { texto = it }, label = { Text("Texto") }, modifier = Modifier.fillMaxWidth(), minLines = 3)
            },
            confirmButton = {
                TextButton(onClick = {
                    vm.agregarObservacion(texto) { ok, _ -> if (ok) showObservacionDialog = false }
                }) { Text("Agregar") }
            },
            dismissButton = { TextButton(onClick = { showObservacionDialog = false }) { Text("Cancelar") } }
        )
    }

    if (showRepuestoDialog) {
        AgregarRepuestoDialog(
            repuestos = repuestos,
            onDismiss = { showRepuestoDialog = false },
            onConfirm = { repId, cant ->
                vm.agregarRepuesto(repId, cant) { ok, _ -> if (ok) showRepuestoDialog = false }
            }
        )
    }

    if (showConfirmEliminarFoto != null) {
        ConfirmDialog(
            title = "Eliminar foto",
            text = "¿Seguro que querés eliminar esta foto?",
            onConfirm = { vm.eliminarFoto(showConfirmEliminarFoto!!); showConfirmEliminarFoto = null },
            onDismiss = { showConfirmEliminarFoto = null }
        )
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun AgregarRepuestoDialog(
    repuestos: List<RepuestoDisponibleDto>,
    onDismiss: () -> Unit,
    onConfirm: (Int, Double) -> Unit
) {
    var repId by remember { mutableStateOf<Int?>(null) }
    var cantidad by remember { mutableStateOf("1") }
    var expanded by remember { mutableStateOf(false) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Agregar repuesto") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                ExposedDropdownMenuBox(expanded = expanded, onExpandedChange = { expanded = it }) {
                    OutlinedTextField(
                        value = repuestos.find { it.id == repId }?.nombre ?: "Seleccionar repuesto",
                        onValueChange = {},
                        readOnly = true,
                        label = { Text("Repuesto") },
                        trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded) },
                        modifier = Modifier.menuAnchor().fillMaxWidth()
                    )
                    ExposedDropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
                        repuestos.forEach { rep ->
                            DropdownMenuItem(
                                text = { Text("${rep.nombre} (stock: ${rep.stockActual})") },
                                onClick = { repId = rep.id; expanded = false }
                            )
                        }
                    }
                }
                OutlinedTextField(
                    value = cantidad,
                    onValueChange = { cantidad = it },
                    label = { Text("Cantidad") },
                    modifier = Modifier.fillMaxWidth()
                )
            }
        },
        confirmButton = {
            TextButton(
                onClick = { repId?.let { onConfirm(it, cantidad.toDoubleOrNull() ?: 1.0) } },
                enabled = repId != null
            ) { Text("Agregar") }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancelar") } }
    )
}
