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
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import coil.compose.AsyncImage
import com.example.mantenimientoapp.data.preferences.SessionManager
import com.example.mantenimientoapp.data.remote.ApiService
import com.example.mantenimientoapp.data.remote.dto.RepuestoConsolidadoItemDto
import com.example.mantenimientoapp.utils.NetworkResult
import com.example.mantenimientoapp.utils.safeApiCall
import com.example.mantenimientoapp.ui.components.ErrorBox
import com.example.mantenimientoapp.ui.components.LoadingBox
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import javax.inject.Inject

data class ConsolidadoUiState(
    val loading: Boolean = true,
    val error: String? = null,
    val items: List<RepuestoConsolidadoItemDto> = emptyList()
)

@HiltViewModel
class ConsolidadoViewModel @Inject constructor(
    private val api: ApiService,
    private val session: SessionManager
) : ViewModel() {
    private val _state = MutableStateFlow(ConsolidadoUiState())
    val state: StateFlow<ConsolidadoUiState> = _state.asStateFlow()
    val baseUrl: StateFlow<String> = session.baseUrl.stateIn(viewModelScope, SharingStarted.WhileSubscribed(), "")

    init { load() }

    fun load() {
        viewModelScope.launch {
            _state.value = ConsolidadoUiState(loading = true)
            when (val r = safeApiCall { api.getRepuestosConsolidado() }) {
                is NetworkResult.Success -> _state.value = ConsolidadoUiState(loading = false, items = r.data)
                is NetworkResult.Error -> _state.value = ConsolidadoUiState(loading = false, error = r.message)
                else -> {}
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ConsolidadoRepuestosScreen(
    onBack: () -> Unit,
    vm: ConsolidadoViewModel = hiltViewModel()
) {
    val state by vm.state.collectAsState()
    val baseUrl by vm.baseUrl.collectAsState()
    val enAlerta = state.items.count { it.enAlerta }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Stock consolidado${if (enAlerta > 0) " ($enAlerta alertas)" else ""}") },
                navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, null) } },
                actions = { IconButton(onClick = { vm.load() }) { Icon(Icons.Default.Refresh, null) } }
            )
        }
    ) { padding ->
        when {
            state.loading -> LoadingBox(Modifier.padding(padding))
            state.error != null -> ErrorBox(state.error!!, onRetry = { vm.load() }, modifier = Modifier.padding(padding))
            state.items.isEmpty() -> Box(Modifier.padding(padding).fillMaxSize(), contentAlignment = Alignment.Center) {
                Text("Sin repuestos en el sistema", color = MaterialTheme.colorScheme.outline)
            }
            else -> LazyColumn(Modifier.padding(padding), contentPadding = PaddingValues(12.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                items(state.items, key = { it.repuestoId }) { item ->
                    ConsolidadoCard(item = item, baseUrl = baseUrl)
                }
            }
        }
    }
}

@Composable
private fun ConsolidadoCard(item: RepuestoConsolidadoItemDto, baseUrl: String) {
    var expanded by remember { mutableStateOf(false) }
    val alertColor = Color(0xFFEF4444)
    val okColor = Color(0xFF10B981)

    Card(
        modifier = Modifier.fillMaxWidth(),
        border = if (item.enAlerta) androidx.compose.foundation.BorderStroke(2.dp, alertColor) else null
    ) {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                if (item.tieneImagen) {
                    AsyncImage(
                        model = "$baseUrl/api/admin/repuestos/${item.repuestoId}/imagen",
                        contentDescription = null,
                        modifier = Modifier.size(48.dp),
                        contentScale = ContentScale.Crop
                    )
                } else {
                    Icon(Icons.Default.Inventory, null, Modifier.size(48.dp), tint = MaterialTheme.colorScheme.outline)
                }
                Column(Modifier.weight(1f)) {
                    Text(item.repuestoNombre, style = MaterialTheme.typography.titleMedium)
                    if (item.repuestoDescripcion.isNotBlank()) {
                        Text(item.repuestoDescripcion, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
                    }
                }
                Surface(
                    shape = MaterialTheme.shapes.small,
                    color = if (item.enAlerta) alertColor else okColor
                ) {
                    Text(
                        if (item.enAlerta) "⚠ BAJO" else "✓ OK",
                        Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                        style = MaterialTheme.typography.labelSmall,
                        color = Color.White
                    )
                }
            }

            Row(horizontalArrangement = Arrangement.spacedBy(24.dp)) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text("${item.stockActual}", style = MaterialTheme.typography.titleLarge, color = if (item.enAlerta) alertColor else MaterialTheme.colorScheme.onSurface)
                    Text("Stock actual", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.outline)
                }
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text("${item.sumaMinimos}", style = MaterialTheme.typography.titleLarge)
                    Text("Suma mínimos", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.outline)
                }
            }

            if (item.equipos.isNotEmpty()) {
                TextButton(onClick = { expanded = !expanded }, contentPadding = PaddingValues(0.dp)) {
                    Icon(if (expanded) Icons.Default.ExpandLess else Icons.Default.ExpandMore, null, Modifier.size(16.dp))
                    Spacer(Modifier.width(4.dp))
                    Text("${item.equipos.size} equipo(s)", style = MaterialTheme.typography.labelMedium)
                }
                if (expanded) {
                    item.equipos.forEach { e ->
                        Row(Modifier.padding(start = 8.dp, bottom = 2.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Text("•", color = MaterialTheme.colorScheme.outline)
                            Text(e.equipoNombre, style = MaterialTheme.typography.bodySmall, modifier = Modifier.weight(1f))
                            Text("mín: ${e.stockMinimo}", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
                        }
                    }
                }
            }
        }
    }
}
