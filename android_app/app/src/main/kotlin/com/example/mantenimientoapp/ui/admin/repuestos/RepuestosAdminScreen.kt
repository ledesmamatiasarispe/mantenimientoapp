package com.example.mantenimientoapp.ui.admin.repuestos

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
import com.example.mantenimientoapp.data.preferences.SessionManager
import com.example.mantenimientoapp.data.remote.dto.AdminRepuestoItemDto
import com.example.mantenimientoapp.data.remote.dto.AdminRepuestoRequestDto
import com.example.mantenimientoapp.ui.admin.RepuestosAdminViewModel
import com.example.mantenimientoapp.ui.components.*
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import androidx.hilt.navigation.compose.hiltViewModel as hiltViewModel1
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.stateIn
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.StateFlow

// Helper ViewModel solo para la URL base (para las imágenes)
@HiltViewModel
class RepuestosAdminUrlViewModel @Inject constructor(session: SessionManager) : ViewModel() {
    val baseUrl: StateFlow<String> = session.baseUrl
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(), "")
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RepuestosAdminScreen(
    onBack: () -> Unit,
    vm: RepuestosAdminViewModel = hiltViewModel(),
    urlVm: RepuestosAdminUrlViewModel = hiltViewModel()
) {
    val state by vm.state.collectAsState()
    val baseUrl by urlVm.baseUrl.collectAsState()
    var showDialog by remember { mutableStateOf<AdminRepuestoItemDto?>(null) }
    var showNew by remember { mutableStateOf(false) }
    var confirmDelete by remember { mutableStateOf<Int?>(null) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Repuestos") },
                navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, "Volver") } }
            )
        },
        floatingActionButton = {
            FloatingActionButton(onClick = { showNew = true }) { Icon(Icons.Default.Add, "Nuevo repuesto") }
        }
    ) { padding ->
        Column(Modifier.padding(padding)) {
            when {
                state.loading -> LoadingBox()
                state.error != null -> ErrorBox(state.error!!, onRetry = { vm.load() })
                else -> LazyColumn(contentPadding = PaddingValues(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    items(state.repuestos, key = { it.id }) { rep ->
                        RepuestoItem(
                            rep = rep,
                            baseUrl = baseUrl,
                            onEdit = { showDialog = rep },
                            onDelete = { confirmDelete = rep.id }
                        )
                    }
                }
            }
        }
    }

    if (showNew) {
        RepuestoDialog(onDismiss = { showNew = false }, onConfirm = { req -> vm.crear(req) { ok, _ -> if (ok) showNew = false } })
    }
    if (showDialog != null) {
        RepuestoDialog(repuesto = showDialog, onDismiss = { showDialog = null }, onConfirm = { req -> vm.actualizar(showDialog!!.id, req) { ok, _ -> if (ok) showDialog = null } })
    }
    if (confirmDelete != null) {
        ConfirmDialog("Eliminar repuesto", "¿Seguro?",
            onConfirm = { vm.eliminar(confirmDelete!!); confirmDelete = null },
            onDismiss = { confirmDelete = null })
    }
}

@Composable
private fun RepuestoItem(rep: AdminRepuestoItemDto, baseUrl: String, onEdit: () -> Unit, onDelete: () -> Unit) {
    Card(Modifier.fillMaxWidth()) {
        Row(Modifier.padding(12.dp), horizontalArrangement = Arrangement.spacedBy(10.dp), verticalAlignment = Alignment.CenterVertically) {
            if (rep.tieneImagen) {
                AsyncImage(
                    model = "$baseUrl/api/admin/repuestos/${rep.id}/imagen",
                    contentDescription = null,
                    modifier = Modifier.size(48.dp),
                    contentScale = ContentScale.Crop
                )
            } else {
                Icon(Icons.Default.Inventory, null, Modifier.size(40.dp), tint = MaterialTheme.colorScheme.outline)
            }
            Column(Modifier.weight(1f)) {
                Text(rep.nombre, style = MaterialTheme.typography.titleSmall)
                if (rep.descripcion.isNotBlank()) Text(rep.descripcion, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
                Text("Stock: ${rep.stockActual}", style = MaterialTheme.typography.bodySmall)
                if (rep.observaciones.isNotBlank()) Text(rep.observaciones, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
            }
            Row {
                IconButton(onClick = onEdit) { Icon(Icons.Default.Edit, null, Modifier.size(18.dp)) }
                IconButton(onClick = onDelete) { Icon(Icons.Default.Delete, null, Modifier.size(18.dp), tint = MaterialTheme.colorScheme.error) }
            }
        }
    }
}

@Composable
private fun RepuestoDialog(
    repuesto: AdminRepuestoItemDto? = null,
    onDismiss: () -> Unit,
    onConfirm: (AdminRepuestoRequestDto) -> Unit
) {
    var nombre by remember { mutableStateOf(repuesto?.nombre ?: "") }
    var descripcion by remember { mutableStateOf(repuesto?.descripcion ?: "") }
    var obs by remember { mutableStateOf(repuesto?.observaciones ?: "") }
    var stockActual by remember { mutableStateOf(repuesto?.stockActual?.toString() ?: "0") }
    var activo by remember { mutableStateOf(repuesto?.activo ?: true) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(if (repuesto == null) "Nuevo repuesto" else "Editar repuesto") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                OutlinedTextField(value = nombre, onValueChange = { nombre = it }, label = { Text("Nombre *") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = descripcion, onValueChange = { descripcion = it }, label = { Text("Descripción") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = obs, onValueChange = { obs = it }, label = { Text("Observaciones internas") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = stockActual, onValueChange = { stockActual = it }, label = { Text("Stock actual") }, modifier = Modifier.fillMaxWidth())
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Checkbox(checked = activo, onCheckedChange = { activo = it })
                    Text("Activo")
                }
            }
        },
        confirmButton = {
            TextButton(
                onClick = { onConfirm(AdminRepuestoRequestDto(nombre, descripcion, obs, stockActual.toDoubleOrNull() ?: 0.0, activo)) },
                enabled = nombre.isNotBlank()
            ) { Text("Guardar") }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancelar") } }
    )
}
