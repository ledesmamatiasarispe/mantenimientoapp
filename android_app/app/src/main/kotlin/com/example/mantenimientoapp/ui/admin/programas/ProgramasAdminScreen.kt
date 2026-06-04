package com.example.mantenimientoapp.ui.admin.programas

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
import com.example.mantenimientoapp.data.remote.dto.AdminProgramaItemDto
import com.example.mantenimientoapp.data.remote.dto.AdminProgramaRequestDto
import com.example.mantenimientoapp.data.remote.dto.EquipoCardDto
import com.example.mantenimientoapp.ui.admin.ProgramasAdminViewModel
import com.example.mantenimientoapp.ui.components.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ProgramasAdminScreen(
    onBack: () -> Unit,
    vm: ProgramasAdminViewModel = hiltViewModel()
) {
    val state by vm.state.collectAsState()
    var showNew by remember { mutableStateOf(false) }
    var showEdit by remember { mutableStateOf<AdminProgramaItemDto?>(null) }
    var confirmDelete by remember { mutableStateOf<Int?>(null) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Programas de mantenimiento") },
                navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, "Volver") } }
            )
        },
        floatingActionButton = {
            FloatingActionButton(onClick = { showNew = true }) { Icon(Icons.Default.Add, "Nuevo programa") }
        }
    ) { padding ->
        Column(Modifier.padding(padding)) {
            when {
                state.loading -> LoadingBox()
                state.error != null -> ErrorBox(state.error!!, onRetry = { vm.load() })
                else -> LazyColumn(contentPadding = PaddingValues(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    items(state.programas, key = { it.id }) { prog ->
                        ProgramaItem(prog, onEdit = { showEdit = prog }, onDelete = { confirmDelete = prog.id })
                    }
                }
            }
        }
    }

    if (showNew) {
        ProgramaDialog(equipos = state.equipos, onDismiss = { showNew = false }, onConfirm = { req -> vm.crear(req) { ok, _ -> if (ok) showNew = false } })
    }
    if (showEdit != null) {
        ProgramaDialog(programa = showEdit, equipos = state.equipos, onDismiss = { showEdit = null }, onConfirm = { req -> vm.actualizar(showEdit!!.id, req) { ok, _ -> if (ok) showEdit = null } })
    }
    if (confirmDelete != null) {
        ConfirmDialog("Eliminar programa", "¿Seguro?", onConfirm = { vm.eliminar(confirmDelete!!); confirmDelete = null }, onDismiss = { confirmDelete = null })
    }
}

@Composable
private fun ProgramaItem(prog: AdminProgramaItemDto, onEdit: () -> Unit, onDelete: () -> Unit) {
    Card(Modifier.fillMaxWidth()) {
        Row(Modifier.padding(12.dp), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Text(prog.descripcion, style = MaterialTheme.typography.titleSmall)
                Text(prog.equipoNombre, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
                Text("Cada ${prog.frecuenciaMeses} meses · Próxima: ${prog.proximaEjecucion.take(10)}", style = MaterialTheme.typography.bodySmall)
                if (!prog.activo) Text("Inactivo", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.error)
            }
            Row {
                IconButton(onClick = onEdit) { Icon(Icons.Default.Edit, null, Modifier.size(18.dp)) }
                IconButton(onClick = onDelete) { Icon(Icons.Default.Delete, null, Modifier.size(18.dp), tint = MaterialTheme.colorScheme.error) }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ProgramaDialog(
    programa: AdminProgramaItemDto? = null,
    equipos: List<EquipoCardDto>,
    onDismiss: () -> Unit,
    onConfirm: (AdminProgramaRequestDto) -> Unit
) {
    var descripcion by remember { mutableStateOf(programa?.descripcion ?: "") }
    var equipoId by remember { mutableStateOf(programa?.equipoId) }
    var frecuencia by remember { mutableStateOf(programa?.frecuenciaMeses?.toString() ?: "12") }
    var ultimaEjec by remember { mutableStateOf(programa?.ultimaEjecucion?.take(10) ?: "") }
    var activo by remember { mutableStateOf(programa?.activo ?: true) }
    var expandedEquipo by remember { mutableStateOf(false) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(if (programa == null) "Nuevo programa" else "Editar programa") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                OutlinedTextField(value = descripcion, onValueChange = { descripcion = it }, label = { Text("Descripción *") }, modifier = Modifier.fillMaxWidth())

                ExposedDropdownMenuBox(expanded = expandedEquipo, onExpandedChange = { expandedEquipo = it }) {
                    OutlinedTextField(
                        value = equipos.find { it.id == equipoId }?.nombre ?: "Seleccionar equipo",
                        onValueChange = {}, readOnly = true, label = { Text("Equipo *") },
                        trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expandedEquipo) },
                        modifier = Modifier.menuAnchor().fillMaxWidth()
                    )
                    ExposedDropdownMenu(expanded = expandedEquipo, onDismissRequest = { expandedEquipo = false }) {
                        equipos.forEach { eq -> DropdownMenuItem(text = { Text(eq.nombre) }, onClick = { equipoId = eq.id; expandedEquipo = false }) }
                    }
                }

                OutlinedTextField(value = frecuencia, onValueChange = { frecuencia = it }, label = { Text("Frecuencia (meses)") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = ultimaEjec, onValueChange = { ultimaEjec = it }, label = { Text("Última ejecución (AAAA-MM-DD)") }, modifier = Modifier.fillMaxWidth())
                Row(verticalAlignment = Alignment.CenterVertically) { Checkbox(checked = activo, onCheckedChange = { activo = it }); Text("Activo") }
            }
        },
        confirmButton = {
            TextButton(
                onClick = { equipoId?.let { id -> onConfirm(AdminProgramaRequestDto(id, descripcion, frecuencia.toIntOrNull() ?: 12, ultimaEjec, activo)) } },
                enabled = descripcion.isNotBlank() && equipoId != null
            ) { Text("Guardar") }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancelar") } }
    )
}
