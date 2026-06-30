package com.example.mantenimientoapp.ui.admin.proveedores

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
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.mantenimientoapp.data.remote.ApiService
import com.example.mantenimientoapp.data.remote.dto.ProveedorItemDto
import com.example.mantenimientoapp.data.remote.dto.ProveedorRequestDto
import com.example.mantenimientoapp.utils.NetworkResult
import com.example.mantenimientoapp.utils.safeApiCall
import com.example.mantenimientoapp.ui.components.*
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

data class ProveedoresUiState(
    val loading: Boolean = true,
    val error: String? = null,
    val proveedores: List<ProveedorItemDto> = emptyList()
)

@HiltViewModel
class ProveedoresAdminViewModel @Inject constructor(private val api: ApiService) : ViewModel() {
    private val _state = MutableStateFlow(ProveedoresUiState())
    val state: StateFlow<ProveedoresUiState> = _state.asStateFlow()

    init { load() }

    fun load() {
        viewModelScope.launch {
            _state.value = ProveedoresUiState(loading = true)
            when (val r = safeApiCall { api.getProveedores() }) {
                is NetworkResult.Success -> _state.value = ProveedoresUiState(loading = false, proveedores = r.data)
                is NetworkResult.Error -> _state.value = ProveedoresUiState(loading = false, error = r.message)
                else -> {}
            }
        }
    }

    fun crear(req: ProveedorRequestDto, onDone: (Boolean, String?) -> Unit) {
        viewModelScope.launch {
            when (val r = safeApiCall { api.crearProveedor(req) }) {
                is NetworkResult.Success -> { load(); onDone(true, null) }
                is NetworkResult.Error -> onDone(false, r.message)
                else -> {}
            }
        }
    }

    fun actualizar(id: Int, req: ProveedorRequestDto, onDone: (Boolean, String?) -> Unit) {
        viewModelScope.launch {
            when (val r = safeApiCall { api.actualizarProveedor(id, req) }) {
                is NetworkResult.Success -> { load(); onDone(true, null) }
                is NetworkResult.Error -> onDone(false, r.message)
                else -> {}
            }
        }
    }

    fun eliminar(id: Int) {
        viewModelScope.launch { safeApiCall { api.eliminarProveedor(id) }; load() }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ProveedoresAdminScreen(onBack: () -> Unit, vm: ProveedoresAdminViewModel = hiltViewModel()) {
    val state by vm.state.collectAsState()
    var showNew by remember { mutableStateOf(false) }
    var showEdit by remember { mutableStateOf<ProveedorItemDto?>(null) }
    var confirmDelete by remember { mutableStateOf<Int?>(null) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Proveedores") },
                navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, null) } },
                actions = { IconButton(onClick = { vm.load() }) { Icon(Icons.Default.Refresh, null) } }
            )
        },
        floatingActionButton = { FloatingActionButton(onClick = { showNew = true }) { Icon(Icons.Default.Add, "Nuevo proveedor") } }
    ) { padding ->
        when {
            state.loading -> LoadingBox(Modifier.padding(padding))
            state.error != null -> ErrorBox(state.error!!, onRetry = { vm.load() }, modifier = Modifier.padding(padding))
            state.proveedores.isEmpty() -> Box(Modifier.padding(padding).fillMaxSize(), contentAlignment = Alignment.Center) {
                Text("Sin proveedores registrados", color = MaterialTheme.colorScheme.outline)
            }
            else -> LazyColumn(Modifier.padding(padding), contentPadding = PaddingValues(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                items(state.proveedores, key = { it.id }) { prov ->
                    ProveedorCard(prov, onEdit = { showEdit = prov }, onDelete = { confirmDelete = prov.id })
                }
            }
        }
    }

    if (showNew) ProveedorDialog(onDismiss = { showNew = false }, onConfirm = { req -> vm.crear(req) { ok, _ -> if (ok) showNew = false } })
    showEdit?.let { p -> ProveedorDialog(proveedor = p, onDismiss = { showEdit = null }, onConfirm = { req -> vm.actualizar(p.id, req) { ok, _ -> if (ok) showEdit = null } }) }
    confirmDelete?.let { id -> ConfirmDialog("Eliminar proveedor", "¿Seguro?", onConfirm = { vm.eliminar(id); confirmDelete = null }, onDismiss = { confirmDelete = null }) }
}

@Composable
private fun ProveedorCard(prov: ProveedorItemDto, onEdit: () -> Unit, onDelete: () -> Unit) {
    Card(Modifier.fillMaxWidth()) {
        Row(Modifier.padding(12.dp), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(3.dp)) {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                    Text(prov.nombre, style = MaterialTheme.typography.titleSmall)
                    if (!prov.activo) Surface(shape = MaterialTheme.shapes.small, color = MaterialTheme.colorScheme.errorContainer) {
                        Text("Inactivo", Modifier.padding(horizontal = 6.dp, vertical = 2.dp), style = MaterialTheme.typography.labelSmall)
                    }
                }
                if (prov.cuit.isNotBlank()) Text("CUIT: ${prov.cuit}", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
                if (prov.contacto.isNotBlank()) Text(prov.contacto, style = MaterialTheme.typography.bodySmall)
                if (prov.telefono.isNotBlank()) Text("📞 ${prov.telefono}", style = MaterialTheme.typography.bodySmall)
                if (prov.email.isNotBlank()) Text("✉ ${prov.email}", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
            }
            Row {
                IconButton(onClick = onEdit) { Icon(Icons.Default.Edit, null, Modifier.size(18.dp)) }
                IconButton(onClick = onDelete) { Icon(Icons.Default.Delete, null, Modifier.size(18.dp), tint = MaterialTheme.colorScheme.error) }
            }
        }
    }
}

@Composable
private fun ProveedorDialog(proveedor: ProveedorItemDto? = null, onDismiss: () -> Unit, onConfirm: (ProveedorRequestDto) -> Unit) {
    var nombre by remember { mutableStateOf(proveedor?.nombre ?: "") }
    var cuit by remember { mutableStateOf(proveedor?.cuit ?: "") }
    var contacto by remember { mutableStateOf(proveedor?.contacto ?: "") }
    var telefono by remember { mutableStateOf(proveedor?.telefono ?: "") }
    var email by remember { mutableStateOf(proveedor?.email ?: "") }
    var direccion by remember { mutableStateOf(proveedor?.direccion ?: "") }
    var notas by remember { mutableStateOf(proveedor?.notas ?: "") }
    var activo by remember { mutableStateOf(proveedor?.activo ?: true) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(if (proveedor == null) "Nuevo proveedor" else "Editar proveedor") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(9.dp)) {
                OutlinedTextField(value = nombre, onValueChange = { nombre = it }, label = { Text("Nombre *") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = cuit, onValueChange = { cuit = it }, label = { Text("CUIT") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = contacto, onValueChange = { contacto = it }, label = { Text("Contacto") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = telefono, onValueChange = { telefono = it }, label = { Text("Teléfono") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = email, onValueChange = { email = it }, label = { Text("Email") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = direccion, onValueChange = { direccion = it }, label = { Text("Dirección") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = notas, onValueChange = { notas = it }, label = { Text("Notas / condiciones") }, modifier = Modifier.fillMaxWidth(), minLines = 2)
                Row(verticalAlignment = Alignment.CenterVertically) { Checkbox(checked = activo, onCheckedChange = { activo = it }); Text("Activo") }
            }
        },
        confirmButton = {
            TextButton(onClick = { onConfirm(ProveedorRequestDto(nombre, cuit, contacto, telefono, email, direccion, notas, activo)) }, enabled = nombre.isNotBlank()) { Text("Guardar") }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancelar") } }
    )
}
