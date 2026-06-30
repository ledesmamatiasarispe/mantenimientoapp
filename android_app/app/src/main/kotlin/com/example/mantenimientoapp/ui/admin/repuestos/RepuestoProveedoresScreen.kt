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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.mantenimientoapp.data.remote.ApiService
import com.example.mantenimientoapp.data.remote.dto.*
import com.example.mantenimientoapp.utils.NetworkResult
import com.example.mantenimientoapp.utils.safeApiCall
import com.example.mantenimientoapp.ui.components.*
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

data class RepuestoProveedoresUiState(
    val loading: Boolean = true,
    val error: String? = null,
    val vinculos: List<RepuestoProveedorItemDto> = emptyList(),
    val catalogo: List<ProveedorItemDto> = emptyList()
)

@HiltViewModel
class RepuestoProveedoresViewModel @Inject constructor(private val api: ApiService) : ViewModel() {
    private val _state = MutableStateFlow(RepuestoProveedoresUiState())
    val state: StateFlow<RepuestoProveedoresUiState> = _state.asStateFlow()

    fun load(repuestoId: Int) {
        viewModelScope.launch {
            _state.value = RepuestoProveedoresUiState(loading = true)
            val vinc = safeApiCall { api.getRepuestoProveedores(repuestoId) }
            val cat = safeApiCall { api.getProveedores() }
            if (vinc is NetworkResult.Success && cat is NetworkResult.Success) {
                _state.value = RepuestoProveedoresUiState(loading = false, vinculos = vinc.data, catalogo = cat.data)
            } else {
                _state.value = RepuestoProveedoresUiState(loading = false, error = (vinc as? NetworkResult.Error)?.message ?: "Error")
            }
        }
    }

    fun marcarPrincipal(repuestoId: Int, vinculoId: Int) {
        viewModelScope.launch { safeApiCall { api.actualizarVinculoProveedor(repuestoId, vinculoId, RepuestoProveedorUpdateDto(true)) }; load(repuestoId) }
    }

    fun vincular(repuestoId: Int, proveedorId: Int, esPrincipal: Boolean, onDone: (Boolean, String?) -> Unit) {
        viewModelScope.launch {
            when (val r = safeApiCall { api.vincularProveedor(repuestoId, RepuestoProveedorRequestDto(proveedorId, esPrincipal)) }) {
                is NetworkResult.Success -> { load(repuestoId); onDone(true, null) }
                is NetworkResult.Error -> onDone(false, r.message)
                else -> {}
            }
        }
    }

    fun desvincular(repuestoId: Int, vinculoId: Int) {
        viewModelScope.launch { safeApiCall { api.desvincularProveedor(repuestoId, vinculoId) }; load(repuestoId) }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RepuestoProveedoresScreen(
    repuestoId: Int,
    repuestoNombre: String,
    onBack: () -> Unit,
    vm: RepuestoProveedoresViewModel = hiltViewModel()
) {
    val state by vm.state.collectAsState()
    var showAgregar by remember { mutableStateOf(false) }
    var confirmDel by remember { mutableStateOf<Int?>(null) }

    LaunchedEffect(repuestoId) { vm.load(repuestoId) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("$repuestoNombre — Proveedores") },
                navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, null) } },
                actions = { IconButton(onClick = { vm.load(repuestoId) }) { Icon(Icons.Default.Refresh, null) } }
            )
        },
        floatingActionButton = { FloatingActionButton(onClick = { showAgregar = true }) { Icon(Icons.Default.Add, "Vincular") } }
    ) { padding ->
        when {
            state.loading -> LoadingBox(Modifier.padding(padding))
            state.error != null -> ErrorBox(state.error!!, onRetry = { vm.load(repuestoId) }, modifier = Modifier.padding(padding))
            state.vinculos.isEmpty() -> Box(Modifier.padding(padding).fillMaxSize(), contentAlignment = Alignment.Center) {
                Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Sin proveedores vinculados", color = MaterialTheme.colorScheme.outline)
                    TextButton(onClick = { showAgregar = true }) { Text("+ Vincular proveedor") }
                }
            }
            else -> LazyColumn(Modifier.padding(padding), contentPadding = PaddingValues(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                items(state.vinculos, key = { it.id }) { v ->
                    VinculoProveedorCard(
                        v = v,
                        onMarcarPrincipal = { vm.marcarPrincipal(repuestoId, v.id) },
                        onDesvincular = { confirmDel = v.id }
                    )
                }
            }
        }
    }

    if (showAgregar) {
        val disponibles = state.catalogo.filter { c -> c.activo && state.vinculos.none { v -> v.proveedorId == c.id } }
        AgregarProveedorDialog(
            proveedores = disponibles,
            onDismiss = { showAgregar = false },
            onConfirm = { provId, esPrincipal ->
                vm.vincular(repuestoId, provId, esPrincipal) { ok, _ -> if (ok) showAgregar = false }
            }
        )
    }

    confirmDel?.let { vid ->
        ConfirmDialog("Desvincular proveedor", "¿Desvincular este proveedor del repuesto?",
            onConfirm = { vm.desvincular(repuestoId, vid); confirmDel = null },
            onDismiss = { confirmDel = null })
    }
}

@Composable
private fun VinculoProveedorCard(v: RepuestoProveedorItemDto, onMarcarPrincipal: () -> Unit, onDesvincular: () -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        border = if (v.esPrincipal) androidx.compose.foundation.BorderStroke(2.dp, Color(0xFF10B981)) else null
    ) {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text(v.proveedorNombre, style = MaterialTheme.typography.titleSmall)
                    if (v.proveedorContacto.isNotBlank()) Text(v.proveedorContacto, style = MaterialTheme.typography.bodySmall)
                    if (v.proveedorTelefono.isNotBlank()) Text("📞 ${v.proveedorTelefono}", style = MaterialTheme.typography.bodySmall)
                    if (v.proveedorEmail.isNotBlank()) Text("✉ ${v.proveedorEmail}", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
                }
                IconButton(onClick = onDesvincular) { Icon(Icons.Default.Delete, null, Modifier.size(18.dp), tint = MaterialTheme.colorScheme.error) }
            }
            Row(horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth()) {
                if (v.esPrincipal) {
                    Surface(shape = MaterialTheme.shapes.small, color = Color(0xFF10B981)) {
                        Text("⭐ Proveedor principal", Modifier.padding(horizontal = 8.dp, vertical = 4.dp), style = MaterialTheme.typography.labelSmall, color = Color.White)
                    }
                } else {
                    OutlinedButton(onClick = onMarcarPrincipal, contentPadding = PaddingValues(horizontal = 10.dp, vertical = 4.dp)) {
                        Text("Marcar como principal", style = MaterialTheme.typography.labelSmall)
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun AgregarProveedorDialog(proveedores: List<ProveedorItemDto>, onDismiss: () -> Unit, onConfirm: (Int, Boolean) -> Unit) {
    var provId by remember { mutableStateOf<Int?>(null) }
    var esPrincipal by remember { mutableStateOf(false) }
    var expanded by remember { mutableStateOf(false) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Vincular proveedor") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                ExposedDropdownMenuBox(expanded = expanded, onExpandedChange = { expanded = it }) {
                    OutlinedTextField(
                        value = proveedores.find { it.id == provId }?.nombre ?: "Seleccionar proveedor",
                        onValueChange = {}, readOnly = true, label = { Text("Proveedor") },
                        trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded) },
                        modifier = Modifier.menuAnchor().fillMaxWidth()
                    )
                    ExposedDropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
                        if (proveedores.isEmpty()) {
                            DropdownMenuItem(text = { Text("Sin proveedores disponibles", color = MaterialTheme.colorScheme.outline) }, onClick = {})
                        }
                        proveedores.forEach { p ->
                            DropdownMenuItem(text = { Text(p.nombre) }, onClick = { provId = p.id; expanded = false })
                        }
                    }
                }
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Checkbox(checked = esPrincipal, onCheckedChange = { esPrincipal = it })
                    Text("Marcar como proveedor principal")
                }
            }
        },
        confirmButton = {
            TextButton(onClick = { provId?.let { onConfirm(it, esPrincipal) } }, enabled = provId != null) { Text("Vincular") }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancelar") } }
    )
}
