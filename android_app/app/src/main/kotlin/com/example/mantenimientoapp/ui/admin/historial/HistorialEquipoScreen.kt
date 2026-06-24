package com.example.mantenimientoapp.ui.admin.historial

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.mantenimientoapp.data.remote.ApiService
import com.example.mantenimientoapp.data.remote.dto.HistorialEquipoItemDto
import com.example.mantenimientoapp.utils.NetworkResult
import com.example.mantenimientoapp.utils.safeApiCall
import com.example.mantenimientoapp.ui.components.ErrorBox
import com.example.mantenimientoapp.ui.components.EstadoChip
import com.example.mantenimientoapp.ui.components.LoadingBox
import com.example.mantenimientoapp.ui.components.TipoChip
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

data class HistorialUiState(val loading: Boolean = true, val error: String? = null, val items: List<HistorialEquipoItemDto> = emptyList())

@HiltViewModel
class HistorialViewModel @Inject constructor(private val api: ApiService) : ViewModel() {
    private val _state = MutableStateFlow(HistorialUiState())
    val state: StateFlow<HistorialUiState> = _state.asStateFlow()

    fun load(equipoId: Int) {
        viewModelScope.launch {
            _state.value = HistorialUiState(loading = true)
            when (val r = safeApiCall { api.getHistorialEquipo(equipoId) }) {
                is NetworkResult.Success -> _state.value = HistorialUiState(loading = false, items = r.data)
                is NetworkResult.Error -> _state.value = HistorialUiState(loading = false, error = r.message)
                else -> {}
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HistorialEquipoScreen(equipoId: Int, equipoNombre: String, onBack: () -> Unit, onOrdenClick: (Int) -> Unit, vm: HistorialViewModel = hiltViewModel()) {
    val state by vm.state.collectAsState()
    LaunchedEffect(equipoId) { vm.load(equipoId) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Historial: $equipoNombre") },
                navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, null) } },
                actions = { IconButton(onClick = { vm.load(equipoId) }) { Icon(Icons.Default.Refresh, null) } }
            )
        }
    ) { padding ->
        when {
            state.loading -> LoadingBox(Modifier.padding(padding))
            state.error != null -> ErrorBox(state.error!!, onRetry = { vm.load(equipoId) }, modifier = Modifier.padding(padding))
            state.items.isEmpty() -> Box(Modifier.padding(padding).fillMaxSize(), contentAlignment = Alignment.Center) {
                Text("Sin órdenes registradas", color = MaterialTheme.colorScheme.outline)
            }
            else -> LazyColumn(Modifier.padding(padding), contentPadding = PaddingValues(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                items(state.items, key = { it.id }) { h ->
                    Card(onClick = { onOrdenClick(h.id) }, modifier = Modifier.fillMaxWidth()) {
                        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                                Text("#${h.id}", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.outline)
                                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                                    TipoChip(h.tipo)
                                    EstadoChip(h.estado)
                                }
                            }
                            if (h.tecnicoNombre.isNotBlank()) Text(h.tecnicoNombre, style = MaterialTheme.typography.bodySmall)
                            Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                                Text(h.fechaApertura.take(10), style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
                                if (h.horasTrabajo > 0) Text("${h.horasTrabajo}h", style = MaterialTheme.typography.bodySmall)
                                if (h.costoManoObra > 0) Text("$${h.costoManoObra.toInt()}", style = MaterialTheme.typography.bodySmall)
                            }
                        }
                    }
                }
            }
        }
    }
}
