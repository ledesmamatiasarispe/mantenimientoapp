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
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import coil.compose.AsyncImage
import com.example.mantenimientoapp.data.preferences.SessionManager
import com.example.mantenimientoapp.data.remote.ApiService
import com.example.mantenimientoapp.data.remote.dto.*
import com.example.mantenimientoapp.utils.NetworkResult
import com.example.mantenimientoapp.utils.safeApiCall
import com.example.mantenimientoapp.ui.components.*
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

data class RepuestosEquipoUiState(
    val loading: Boolean = true,
    val error: String? = null,
    val vinculos: List<RepuestoEquipoItemDto> = emptyList(),
    val catalogo: List<AdminRepuestoItemDto> = emptyList()
)

@HiltViewModel
class RepuestosEquipoViewModel @Inject constructor(
    private val api: ApiService,
    private val session: SessionManager
) : ViewModel() {
    private val _state = MutableStateFlow(RepuestosEquipoUiState())
    val state: StateFlow<RepuestosEquipoUiState> = _state.asStateFlow()
    val baseUrl: StateFlow<String> = session.baseUrl.stateIn(viewModelScope, SharingStarted.WhileSubscribed(), "")

    fun load(equipoId: Int) {
        viewModelScope.launch {
            _state.value = RepuestosEquipoUiState(loading = true)
            val vinc = safeApiCall { api.getRepuestosEquipo(equipoId) }
            val cat = safeApiCall { api.getAdminRepuestos() }
            if (vinc is NetworkResult.Success && cat is NetworkResult.Success) {
                _state.value = RepuestosEquipoUiState(loading = false, vinculos = vinc.data, catalogo = cat.data)
            } else {
                _state.value = RepuestosEquipoUiState(loading = false, error = (vinc as? NetworkResult.Error)?.message ?: "Error")
            }
        }
    }

    fun vincular(equipoId: Int, repuestoId: Int, minimo: Double, obs: String, onDone: (Boolean, String?) -> Unit) {
        viewModelScope.launch {
            when (val r = safeApiCall { api.vincularRepuesto(equipoId, RepuestoEquipoRequestDto(repuestoId, minimo, obs)) }) {
                is NetworkResult.Success -> { load(equipoId); onDone(true, null) }
                is NetworkResult.Error -> onDone(false, r.message)
                else -> {}
            }
        }
    }

    fun actualizar(equipoId: Int, vinculoId: Int, minimo: Double, obs: String) {
        viewModelScope.launch {
            safeApiCall { api.actualizarVinculo(equipoId, vinculoId, RepuestoEquipoUpdateDto(minimo, obs)) }
            load(equipoId)
        }
    }

    fun desvincular(equipoId: Int, vinculoId: Int) {
        viewModelScope.launch {
            safeApiCall { api.desvincularRepuesto(equipoId, vinculoId) }
            load(equipoId)
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RepuestosEquipoScreen(
    equipoId: Int,
    equipoNombre: String,
    onBack: () -> Unit,
    vm: RepuestosEquipoViewModel = hiltViewModel()
) {
    val state by vm.state.collectAsState()
    val baseUrl by vm.baseUrl.collectAsState()
    var showAgregar by remember { mutableStateOf(false) }
    var editVinculo by remember { mutableStateOf<RepuestoEquipoItemDto?>(null) }
    var confirmDel by remember { mutableStateOf<Int?>(null) }

    LaunchedEffect(equipoId) { vm.load(equipoId) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("$equipoNombre — Repuestos") },
                navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, null) } },
                actions = { IconButton(onClick = { vm.load(equipoId) }) { Icon(Icons.Default.Refresh, null) } }
            )
        },
        floatingActionButton = {
            FloatingActionButton(onClick = { showAgregar = true }) { Icon(Icons.Default.Add, "Vincular repuesto") }
        }
    ) { padding ->
        when {
            state.loading -> LoadingBox(Modifier.padding(padding))
            state.error != null -> ErrorBox(state.error!!, onRetry = { vm.load(equipoId) }, modifier = Modifier.padding(padding))
            else -> {
                if (state.vinculos.isEmpty()) {
                    Box(Modifier.padding(padding).fillMaxSize(), contentAlignment = Alignment.Center) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(8.dp)) {
                            Text("Sin repuestos vinculados", color = MaterialTheme.colorScheme.outline)
                            TextButton(onClick = { showAgregar = true }) { Text("+ Vincular repuesto") }
                        }
                    }
                } else {
                    LazyColumn(Modifier.padding(padding), contentPadding = PaddingValues(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        items(state.vinculos, key = { it.id }) { v ->
                            VinculoCard(
                                vinculo = v,
                                baseUrl = baseUrl,
                                onEdit = { editVinculo = v },
                                onDelete = { confirmDel = v.id }
                            )
                        }
                    }
                }
            }
        }
    }

    if (showAgregar) {
        val disponibles = state.catalogo.filter { c -> c.activo && state.vinculos.none { v -> v.repuestoId == c.id } }
        AgregarVinculoDialog(
            repuestos = disponibles,
            onDismiss = { showAgregar = false },
            onConfirm = { repId, minimo, obs ->
                vm.vincular(equipoId, repId, minimo, obs) { ok, err ->
                    if (ok) showAgregar = false
                    else if (err != null) { /* snackbar */ }
                }
            }
        )
    }

    editVinculo?.let { v ->
        EditVinculoDialog(
            vinculo = v,
            onDismiss = { editVinculo = null },
            onConfirm = { minimo, obs -> vm.actualizar(equipoId, v.id, minimo, obs); editVinculo = null }
        )
    }

    confirmDel?.let { vid ->
        ConfirmDialog(
            title = "Desvincular repuesto",
            text = "¿Desvincular este repuesto del equipo?",
            onConfirm = { vm.desvincular(equipoId, vid); confirmDel = null },
            onDismiss = { confirmDel = null }
        )
    }
}

@Composable
private fun VinculoCard(vinculo: RepuestoEquipoItemDto, baseUrl: String, onEdit: () -> Unit, onDelete: () -> Unit) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            if (vinculo.tieneImagen) {
                AsyncImage(
                    model = "$baseUrl/api/admin/repuestos/${vinculo.repuestoId}/imagen",
                    contentDescription = null,
                    modifier = Modifier.size(48.dp),
                    contentScale = ContentScale.Crop
                )
            } else {
                Icon(Icons.Default.Inventory, null, Modifier.size(40.dp), tint = MaterialTheme.colorScheme.outline)
            }
            Column(Modifier.weight(1f)) {
                Text(vinculo.repuestoNombre, style = MaterialTheme.typography.titleSmall)
                if (vinculo.repuestoDescripcion.isNotBlank()) Text(vinculo.repuestoDescripcion, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
                Text("Mínimo: ${vinculo.stockMinimo}", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.primary)
                if (vinculo.observaciones.isNotBlank()) Text(vinculo.observaciones, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
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
private fun AgregarVinculoDialog(
    repuestos: List<AdminRepuestoItemDto>,
    onDismiss: () -> Unit,
    onConfirm: (Int, Double, String) -> Unit
) {
    var repId by remember { mutableStateOf<Int?>(null) }
    var minimo by remember { mutableStateOf("0") }
    var obs by remember { mutableStateOf("") }
    var expanded by remember { mutableStateOf(false) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Vincular repuesto") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                ExposedDropdownMenuBox(expanded = expanded, onExpandedChange = { expanded = it }) {
                    OutlinedTextField(
                        value = repuestos.find { it.id == repId }?.nombre ?: "Seleccionar repuesto",
                        onValueChange = {}, readOnly = true, label = { Text("Repuesto") },
                        trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded) },
                        modifier = Modifier.menuAnchor().fillMaxWidth()
                    )
                    ExposedDropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
                        repuestos.forEach { r ->
                            DropdownMenuItem(
                                text = { Column { Text(r.nombre); if (r.descripcion.isNotBlank()) Text(r.descripcion, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline) } },
                                onClick = { repId = r.id; expanded = false }
                            )
                        }
                    }
                }
                OutlinedTextField(value = minimo, onValueChange = { minimo = it }, label = { Text("Stock mínimo") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = obs, onValueChange = { obs = it }, label = { Text("Observaciones") }, modifier = Modifier.fillMaxWidth())
            }
        },
        confirmButton = {
            TextButton(
                onClick = { repId?.let { onConfirm(it, minimo.toDoubleOrNull() ?: 0.0, obs) } },
                enabled = repId != null
            ) { Text("Vincular") }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancelar") } }
    )
}

@Composable
private fun EditVinculoDialog(vinculo: RepuestoEquipoItemDto, onDismiss: () -> Unit, onConfirm: (Double, String) -> Unit) {
    var minimo by remember { mutableStateOf(vinculo.stockMinimo.toString()) }
    var obs by remember { mutableStateOf(vinculo.observaciones) }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(vinculo.repuestoNombre) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                OutlinedTextField(value = minimo, onValueChange = { minimo = it }, label = { Text("Stock mínimo") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = obs, onValueChange = { obs = it }, label = { Text("Observaciones") }, modifier = Modifier.fillMaxWidth())
            }
        },
        confirmButton = { TextButton(onClick = { onConfirm(minimo.toDoubleOrNull() ?: 0.0, obs) }) { Text("Guardar") } },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancelar") } }
    )
}
