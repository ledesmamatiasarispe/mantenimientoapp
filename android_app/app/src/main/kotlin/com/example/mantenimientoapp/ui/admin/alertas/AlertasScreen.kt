package com.example.mantenimientoapp.ui.admin.alertas

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
import com.example.mantenimientoapp.data.remote.dto.AlertaItemDto
import com.example.mantenimientoapp.data.remote.dto.SnoozeRequestDto
import com.example.mantenimientoapp.utils.NetworkResult
import com.example.mantenimientoapp.utils.safeApiCall
import com.example.mantenimientoapp.ui.components.ErrorBox
import com.example.mantenimientoapp.ui.components.LoadingBox
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

data class AlertasUiState(
    val loading: Boolean = true,
    val error: String? = null,
    val alertas: List<AlertaItemDto> = emptyList()
)

@HiltViewModel
class AlertasViewModel @Inject constructor(private val api: ApiService) : ViewModel() {
    private val _state = MutableStateFlow(AlertasUiState())
    val state: StateFlow<AlertasUiState> = _state.asStateFlow()

    init { load() }

    fun load() {
        viewModelScope.launch {
            _state.value = AlertasUiState(loading = true)
            when (val r = safeApiCall { api.getAlertas() }) {
                is NetworkResult.Success -> _state.value = AlertasUiState(loading = false, alertas = r.data)
                is NetworkResult.Error -> _state.value = AlertasUiState(loading = false, error = r.message)
                else -> {}
            }
        }
    }

    fun snooze(key: String) {
        viewModelScope.launch {
            safeApiCall { api.snoozeAlerta(key, SnoozeRequestDto(7)) }
            load()
        }
    }

    fun ignorar(key: String) {
        viewModelScope.launch {
            safeApiCall { api.ignorarAlerta(key) }
            load()
        }
    }
}

private data class AlertaTab(val label: String, val tipo: String?, val color: Color)

private val TABS = listOf(
    AlertaTab("Todas", null, Color(0xFF6B7280)),
    AlertaTab("📦 Stock", "STOCK_BAJO", Color(0xFFF97316)),
    AlertaTab("📝 Órdenes", "ORDEN_NUEVA", Color(0xFF3B82F6)),
    AlertaTab("🔧 Mantenimiento", "MANT_VENCIDO", Color(0xFF10B981)),
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AlertasScreen(onBack: () -> Unit, vm: AlertasViewModel = hiltViewModel()) {
    val state by vm.state.collectAsState()
    var selectedTab by remember { mutableStateOf(0) }

    val lista = remember(state.alertas, selectedTab) {
        val tipo = TABS[selectedTab].tipo
        if (tipo == null) state.alertas else state.alertas.filter { it.tipo == tipo }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Alertas (${state.alertas.size})") },
                navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, null) } },
                actions = { IconButton(onClick = { vm.load() }) { Icon(Icons.Default.Refresh, null) } }
            )
        }
    ) { padding ->
        Column(Modifier.padding(padding)) {
            // Tabs con conteo por tipo
            ScrollableTabRow(selectedTabIndex = selectedTab, edgePadding = 0.dp) {
                TABS.forEachIndexed { i, tab ->
                    val count = if (tab.tipo == null) state.alertas.size
                                else state.alertas.count { it.tipo == tab.tipo }
                    Tab(
                        selected = selectedTab == i,
                        onClick = { selectedTab = i }
                    ) {
                        Row(
                            Modifier.padding(horizontal = 12.dp, vertical = 10.dp),
                            horizontalArrangement = Arrangement.spacedBy(6.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(tab.label, style = MaterialTheme.typography.labelMedium)
                            if (count > 0) {
                                Surface(
                                    shape = MaterialTheme.shapes.extraSmall,
                                    color = if (selectedTab == i) tab.color else tab.color.copy(alpha = 0.5f)
                                ) {
                                    Text(
                                        "$count",
                                        Modifier.padding(horizontal = 6.dp, vertical = 1.dp),
                                        style = MaterialTheme.typography.labelSmall,
                                        color = Color.White
                                    )
                                }
                            }
                        }
                    }
                }
            }

            when {
                state.loading -> LoadingBox()
                state.error != null -> ErrorBox(state.error!!, onRetry = { vm.load() })
                lista.isEmpty() -> Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Text("Sin alertas en esta categoría", color = MaterialTheme.colorScheme.outline)
                }
                else -> LazyColumn(
                    contentPadding = PaddingValues(12.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    items(lista, key = { it.key }) { alerta ->
                        AlertaCard(alerta, onSnooze = { vm.snooze(alerta.key) }, onIgnorar = { vm.ignorar(alerta.key) })
                    }
                }
            }
        }
    }
}

@Composable
private fun AlertaCard(alerta: AlertaItemDto, onSnooze: () -> Unit, onIgnorar: () -> Unit) {
    val borderColor = when (alerta.severidad) {
        "alta" -> Color(0xFFEF4444)
        "media" -> Color(0xFFF59E0B)
        else -> Color(0xFF10B981)
    }
    Card(
        modifier = Modifier.fillMaxWidth(),
        border = androidx.compose.foundation.BorderStroke(2.dp, borderColor)
    ) {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(alerta.mensaje, style = MaterialTheme.typography.bodyMedium)
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp), verticalAlignment = Alignment.CenterVertically) {
                Surface(shape = MaterialTheme.shapes.small, color = borderColor.copy(alpha = 0.15f)) {
                    Text(
                        alerta.severidad,
                        Modifier.padding(horizontal = 8.dp, vertical = 3.dp),
                        style = MaterialTheme.typography.labelSmall,
                        color = borderColor
                    )
                }
                Spacer(Modifier.weight(1f))
                OutlinedButton(
                    onClick = onSnooze,
                    contentPadding = PaddingValues(horizontal = 10.dp, vertical = 4.dp)
                ) {
                    Text("Posponer 7d", style = MaterialTheme.typography.labelSmall)
                }
                OutlinedButton(
                    onClick = onIgnorar,
                    contentPadding = PaddingValues(horizontal = 10.dp, vertical = 4.dp)
                ) {
                    Text("Ignorar", style = MaterialTheme.typography.labelSmall)
                }
            }
        }
    }
}
