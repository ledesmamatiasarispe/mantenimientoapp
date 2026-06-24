package com.example.mantenimientoapp.ui.admin.dashboard

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Refresh
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
import com.example.mantenimientoapp.data.remote.dto.DashboardStatsDto
import com.example.mantenimientoapp.utils.NetworkResult
import com.example.mantenimientoapp.utils.safeApiCall
import com.example.mantenimientoapp.ui.components.ErrorBox
import com.example.mantenimientoapp.ui.components.LoadingBox
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

data class DashboardUiState(val loading: Boolean = true, val error: String? = null, val stats: DashboardStatsDto? = null)

@HiltViewModel
class DashboardViewModel @Inject constructor(private val api: ApiService) : ViewModel() {
    private val _state = MutableStateFlow(DashboardUiState())
    val state: StateFlow<DashboardUiState> = _state.asStateFlow()
    init { load() }
    fun load() {
        viewModelScope.launch {
            _state.value = DashboardUiState(loading = true)
            when (val r = safeApiCall { api.getDashboard() }) {
                is NetworkResult.Success -> _state.value = DashboardUiState(loading = false, stats = r.data)
                is NetworkResult.Error -> _state.value = DashboardUiState(loading = false, error = r.message)
                else -> {}
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DashboardScreen(onBack: () -> Unit, vm: DashboardViewModel = hiltViewModel()) {
    val state by vm.state.collectAsState()
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Dashboard") },
                navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, null) } },
                actions = { IconButton(onClick = { vm.load() }) { Icon(Icons.Default.Refresh, null) } }
            )
        }
    ) { padding ->
        when {
            state.loading -> LoadingBox(Modifier.padding(padding))
            state.error != null -> ErrorBox(state.error!!, onRetry = { vm.load() }, modifier = Modifier.padding(padding))
            state.stats != null -> {
                val s = state.stats!!
                LazyVerticalGrid(
                    columns = GridCells.Fixed(2),
                    modifier = Modifier.padding(padding).padding(12.dp),
                    horizontalArrangement = Arrangement.spacedBy(10.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    items(listOf(
                        Triple("Pendientes", s.ordenesPendientes, Color(0xFFF59E0B)),
                        Triple("En progreso", s.ordenesEnProgreso, Color(0xFF3B82F6)),
                        Triple("Completadas (mes)", s.ordenesCompletadasMes, Color(0xFF10B981)),
                        Triple("Equipos activos", s.equiposActivos, Color(0xFF6366F1)),
                        Triple("Alertas activas", s.alertasActivas, Color(0xFFEF4444)),
                        Triple("Stock bajo", s.repuestosBajoStock, Color(0xFFF97316)),
                        Triple("Mant. vencidos", s.programasVencidos, Color(0xFFDC2626)),
                    )) { (label, valor, color) ->
                        Card(border = androidx.compose.foundation.BorderStroke(2.dp, color)) {
                            Column(Modifier.padding(14.dp)) {
                                Text("$valor", style = MaterialTheme.typography.headlineMedium, color = color)
                                Text(label, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
                            }
                        }
                    }
                }
            }
        }
    }
}
