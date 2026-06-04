package com.example.mantenimientoapp.ui.admin.tecnicos

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.example.mantenimientoapp.data.remote.dto.AdminTecnicoCreateDto
import com.example.mantenimientoapp.data.remote.dto.AdminTecnicoItemDto
import com.example.mantenimientoapp.data.remote.dto.AdminTecnicoUpdateDto
import com.example.mantenimientoapp.ui.admin.TecnicosAdminViewModel
import com.example.mantenimientoapp.ui.components.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TecnicosAdminScreen(
    onBack: () -> Unit,
    vm: TecnicosAdminViewModel = hiltViewModel()
) {
    val state by vm.state.collectAsState()
    var showEdit by remember { mutableStateOf<AdminTecnicoItemDto?>(null) }
    var showNew by remember { mutableStateOf(false) }
    var showPassword by remember { mutableStateOf<AdminTecnicoItemDto?>(null) }
    var confirmDelete by remember { mutableStateOf<Int?>(null) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Técnicos") },
                navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, "Volver") } }
            )
        },
        floatingActionButton = {
            FloatingActionButton(onClick = { showNew = true }) { Icon(Icons.Default.Add, "Nuevo técnico") }
        }
    ) { padding ->
        Column(Modifier.padding(padding)) {
            when {
                state.loading -> LoadingBox()
                state.error != null -> ErrorBox(state.error!!, onRetry = { vm.load() })
                else -> LazyColumn(contentPadding = PaddingValues(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    items(state.tecnicos, key = { it.id }) { tec ->
                        TecnicoItem(
                            tec = tec,
                            onEdit = { showEdit = tec },
                            onPassword = { showPassword = tec },
                            onDelete = { confirmDelete = tec.id }
                        )
                    }
                }
            }
        }
    }

    if (showNew) {
        NuevoTecnicoDialog(
            onDismiss = { showNew = false },
            onConfirm = { req -> vm.crear(req) { ok, _ -> if (ok) showNew = false } }
        )
    }
    if (showEdit != null) {
        EditTecnicoDialog(
            tec = showEdit!!,
            onDismiss = { showEdit = null },
            onConfirm = { req -> vm.actualizar(showEdit!!.id, req) { ok, _ -> if (ok) showEdit = null } }
        )
    }
    if (showPassword != null) {
        PasswordDialog(
            nombre = "${showPassword!!.nombre} ${showPassword!!.apellido}",
            onDismiss = { showPassword = null },
            onConfirm = { pwd -> vm.setPassword(showPassword!!.id, pwd) { ok, _ -> if (ok) showPassword = null } }
        )
    }
    if (confirmDelete != null) {
        ConfirmDialog("Eliminar técnico", "¿Seguro?", onConfirm = { vm.eliminar(confirmDelete!!); confirmDelete = null }, onDismiss = { confirmDelete = null })
    }
}

@Composable
private fun TecnicoItem(tec: AdminTecnicoItemDto, onEdit: () -> Unit, onPassword: () -> Unit, onDelete: () -> Unit) {
    Card(Modifier.fillMaxWidth()) {
        Row(Modifier.padding(12.dp), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("${tec.nombre} ${tec.apellido}", style = MaterialTheme.typography.titleSmall)
                    if (!tec.activo) Surface(shape = MaterialTheme.shapes.small, color = MaterialTheme.colorScheme.errorContainer) { Text("Inactivo", Modifier.padding(horizontal = 6.dp, vertical = 2.dp), style = MaterialTheme.typography.labelSmall) }
                }
                Text("Legajo: ${tec.legajo}", style = MaterialTheme.typography.bodySmall)
                if (tec.especialidad.isNotBlank()) Text(tec.especialidad, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
            }
            Row {
                IconButton(onClick = onEdit) { Icon(Icons.Default.Edit, null, Modifier.size(18.dp)) }
                IconButton(onClick = onPassword) { Icon(Icons.Default.Key, null, Modifier.size(18.dp)) }
                IconButton(onClick = onDelete) { Icon(Icons.Default.Delete, null, Modifier.size(18.dp), tint = MaterialTheme.colorScheme.error) }
            }
        }
    }
}

@Composable
private fun NuevoTecnicoDialog(onDismiss: () -> Unit, onConfirm: (AdminTecnicoCreateDto) -> Unit) {
    var nombre by remember { mutableStateOf("") }
    var apellido by remember { mutableStateOf("") }
    var legajo by remember { mutableStateOf("") }
    var telefono by remember { mutableStateOf("") }
    var especialidad by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Nuevo técnico") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                OutlinedTextField(value = nombre, onValueChange = { nombre = it }, label = { Text("Nombre *") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = apellido, onValueChange = { apellido = it }, label = { Text("Apellido *") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = legajo, onValueChange = { legajo = it }, label = { Text("Legajo *") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = telefono, onValueChange = { telefono = it }, label = { Text("Teléfono") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = especialidad, onValueChange = { especialidad = it }, label = { Text("Especialidad") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = password, onValueChange = { password = it }, label = { Text("Contraseña *") }, visualTransformation = PasswordVisualTransformation(), modifier = Modifier.fillMaxWidth())
            }
        },
        confirmButton = {
            TextButton(
                onClick = { onConfirm(AdminTecnicoCreateDto(nombre, apellido, legajo, telefono, especialidad, password)) },
                enabled = nombre.isNotBlank() && apellido.isNotBlank() && legajo.isNotBlank() && password.isNotBlank()
            ) { Text("Crear") }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancelar") } }
    )
}

@Composable
private fun EditTecnicoDialog(tec: AdminTecnicoItemDto, onDismiss: () -> Unit, onConfirm: (AdminTecnicoUpdateDto) -> Unit) {
    var nombre by remember { mutableStateOf(tec.nombre) }
    var apellido by remember { mutableStateOf(tec.apellido) }
    var legajo by remember { mutableStateOf(tec.legajo) }
    var telefono by remember { mutableStateOf(tec.telefono) }
    var especialidad by remember { mutableStateOf(tec.especialidad) }
    var activo by remember { mutableStateOf(tec.activo) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Editar técnico") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                OutlinedTextField(value = nombre, onValueChange = { nombre = it }, label = { Text("Nombre") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = apellido, onValueChange = { apellido = it }, label = { Text("Apellido") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = legajo, onValueChange = { legajo = it }, label = { Text("Legajo") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = telefono, onValueChange = { telefono = it }, label = { Text("Teléfono") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = especialidad, onValueChange = { especialidad = it }, label = { Text("Especialidad") }, modifier = Modifier.fillMaxWidth())
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Checkbox(checked = activo, onCheckedChange = { activo = it })
                    Text("Activo")
                }
            }
        },
        confirmButton = {
            TextButton(onClick = { onConfirm(AdminTecnicoUpdateDto(nombre, apellido, legajo, telefono, especialidad, activo)) }) { Text("Guardar") }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancelar") } }
    )
}

@Composable
private fun PasswordDialog(nombre: String, onDismiss: () -> Unit, onConfirm: (String) -> Unit) {
    var password by remember { mutableStateOf("") }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Cambiar contraseña") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Técnico: $nombre")
                OutlinedTextField(value = password, onValueChange = { password = it }, label = { Text("Nueva contraseña") }, visualTransformation = PasswordVisualTransformation(), modifier = Modifier.fillMaxWidth())
            }
        },
        confirmButton = {
            TextButton(onClick = { onConfirm(password) }, enabled = password.isNotBlank()) { Text("Cambiar") }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancelar") } }
    )
}
