package com.example.mantenimientoapp.ui.admin.equipos

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.example.mantenimientoapp.data.remote.dto.AdminEquipoItemDto
import com.example.mantenimientoapp.data.remote.dto.AdminEquipoRequestDto
import com.example.mantenimientoapp.data.remote.dto.TipoEquipoItemDto
import com.example.mantenimientoapp.ui.admin.EquiposAdminViewModel
import com.example.mantenimientoapp.ui.components.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun EquiposAdminScreen(
    onBack: () -> Unit,
    onHistorial: (Int, String) -> Unit = { _, _ -> },
    onRepuestosEquipo: (Int, String) -> Unit = { _, _ -> },
    vm: EquiposAdminViewModel = hiltViewModel()
) {
    val state by vm.state.collectAsState()
    var showDialog by remember { mutableStateOf<AdminEquipoItemDto?>(null) }
    var showNew by remember { mutableStateOf(false) }
    var confirmDelete by remember { mutableStateOf<Int?>(null) }

    LaunchedEffect(state.actionMsg) {
        if (state.actionMsg != null) {
            kotlinx.coroutines.delay(2000)
            vm.clearMsg()
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Equipos") },
                navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, "Volver") } }
            )
        },
        floatingActionButton = {
            FloatingActionButton(onClick = { showNew = true }) {
                Icon(Icons.Default.Add, "Nuevo equipo")
            }
        }
    ) { padding ->
        Column(Modifier.padding(padding)) {
            if (!state.actionMsg.isNullOrBlank()) {
                LinearProgressIndicator(Modifier.fillMaxWidth())
            }
            when {
                state.loading -> LoadingBox()
                state.error != null -> ErrorBox(state.error!!, onRetry = { vm.load() })
                else -> LazyColumn(contentPadding = PaddingValues(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    items(state.equipos, key = { it.id }) { equipo ->
                        EquipoItem(
                            equipo = equipo,
                            onRepuestos = { onRepuestosEquipo(equipo.id, equipo.nombre) },
                            onHistorial = { onHistorial(equipo.id, equipo.nombre) },
                            onEdit = { showDialog = equipo },
                            onDelete = { confirmDelete = equipo.id }
                        )
                    }
                }
            }
        }
    }

    if (showNew) {
        EquipoDialog(
            tipos = state.tipos,
            onDismiss = { showNew = false },
            onConfirm = { req -> vm.crear(req) { ok, _ -> if (ok) showNew = false } }
        )
    }

    if (showDialog != null) {
        EquipoDialog(
            equipo = showDialog,
            tipos = state.tipos,
            onDismiss = { showDialog = null },
            onConfirm = { req -> vm.actualizar(showDialog!!.id, req) { ok, _ -> if (ok) showDialog = null } }
        )
    }

    if (confirmDelete != null) {
        ConfirmDialog(
            title = "Eliminar equipo",
            text = "¿Seguro que querés eliminar este equipo?",
            onConfirm = { vm.eliminar(confirmDelete!!); confirmDelete = null },
            onDismiss = { confirmDelete = null }
        )
    }
}

@Composable
private fun EquipoItem(equipo: AdminEquipoItemDto, onRepuestos: () -> Unit, onHistorial: () -> Unit, onEdit: () -> Unit, onDelete: () -> Unit) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Row(Modifier.padding(12.dp), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(equipo.nombre, style = MaterialTheme.typography.titleSmall)
                    if (!equipo.activo) {
                        Surface(shape = MaterialTheme.shapes.small, color = MaterialTheme.colorScheme.errorContainer) {
                            Text("Inactivo", Modifier.padding(horizontal = 6.dp, vertical = 2.dp), style = MaterialTheme.typography.labelSmall)
                        }
                    }
                }
                Text(equipo.tipoNombre, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
                if (equipo.marca.isNotBlank() || equipo.modelo.isNotBlank()) {
                    Text("${equipo.marca} ${equipo.modelo}".trim(), style = MaterialTheme.typography.bodySmall)
                }
                if (equipo.ubicacion.isNotBlank()) Text("📍 ${equipo.ubicacion}", style = MaterialTheme.typography.bodySmall)
            }
            Row {
                IconButton(onClick = onRepuestos) { Icon(Icons.Default.Inventory, "Repuestos", Modifier.size(18.dp)) }
                IconButton(onClick = onHistorial) { Icon(Icons.Default.History, "Historial", Modifier.size(18.dp)) }
                IconButton(onClick = onEdit) { Icon(Icons.Default.Edit, "Editar", Modifier.size(18.dp)) }
                IconButton(onClick = onDelete) { Icon(Icons.Default.Delete, "Eliminar", Modifier.size(18.dp), tint = MaterialTheme.colorScheme.error) }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun EquipoDialog(
    equipo: AdminEquipoItemDto? = null,
    tipos: List<TipoEquipoItemDto>,
    onDismiss: () -> Unit,
    onConfirm: (AdminEquipoRequestDto) -> Unit
) {
    var nombre by remember { mutableStateOf(equipo?.nombre ?: "") }
    var tipoId by remember { mutableStateOf(equipo?.tipoId) }
    var serie by remember { mutableStateOf(equipo?.numeroSerie ?: "") }
    var marca by remember { mutableStateOf(equipo?.marca ?: "") }
    var modelo by remember { mutableStateOf(equipo?.modelo ?: "") }
    var ubicacion by remember { mutableStateOf(equipo?.ubicacion ?: "") }
    var observaciones by remember { mutableStateOf(equipo?.observaciones ?: "") }
    var activo by remember { mutableStateOf(equipo?.activo ?: true) }
    var expandedTipo by remember { mutableStateOf(false) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(if (equipo == null) "Nuevo equipo" else "Editar equipo") },
        text = {
            LazyColumn(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                item {
                    OutlinedTextField(value = nombre, onValueChange = { nombre = it }, label = { Text("Nombre *") }, modifier = Modifier.fillMaxWidth())
                }
                item {
                    ExposedDropdownMenuBox(expanded = expandedTipo, onExpandedChange = { expandedTipo = it }) {
                        OutlinedTextField(
                            value = tipos.find { it.id == tipoId }?.nombre ?: "Sin tipo",
                            onValueChange = {},
                            readOnly = true,
                            label = { Text("Tipo") },
                            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expandedTipo) },
                            modifier = Modifier.menuAnchor().fillMaxWidth()
                        )
                        ExposedDropdownMenu(expanded = expandedTipo, onDismissRequest = { expandedTipo = false }) {
                            DropdownMenuItem(text = { Text("Sin tipo") }, onClick = { tipoId = null; expandedTipo = false })
                            tipos.filter { it.activo }.forEach { t ->
                                DropdownMenuItem(text = { Text(t.nombre) }, onClick = { tipoId = t.id; expandedTipo = false })
                            }
                        }
                    }
                }
                item { OutlinedTextField(value = marca, onValueChange = { marca = it }, label = { Text("Marca") }, modifier = Modifier.fillMaxWidth()) }
                item { OutlinedTextField(value = modelo, onValueChange = { modelo = it }, label = { Text("Modelo") }, modifier = Modifier.fillMaxWidth()) }
                item { OutlinedTextField(value = serie, onValueChange = { serie = it }, label = { Text("Nº Serie") }, modifier = Modifier.fillMaxWidth()) }
                item { OutlinedTextField(value = ubicacion, onValueChange = { ubicacion = it }, label = { Text("Ubicación") }, modifier = Modifier.fillMaxWidth()) }
                item { OutlinedTextField(value = observaciones, onValueChange = { observaciones = it }, label = { Text("Observaciones") }, modifier = Modifier.fillMaxWidth(), minLines = 2) }
                item {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Checkbox(checked = activo, onCheckedChange = { activo = it })
                        Text("Activo")
                    }
                }
            }
        },
        confirmButton = {
            TextButton(
                onClick = {
                    onConfirm(AdminEquipoRequestDto(nombre, tipoId, serie, marca, modelo, ubicacion, "", observaciones, activo))
                },
                enabled = nombre.isNotBlank()
            ) { Text("Guardar") }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancelar") } }
    )
}
