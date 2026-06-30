package com.example.mantenimientoapp.ui.admin.generar

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.mantenimientoapp.data.remote.ApiService
import com.example.mantenimientoapp.data.remote.dto.GenerarOrdenesRequestDto
import com.example.mantenimientoapp.data.remote.dto.GenerarOrdenesResultDto
import com.example.mantenimientoapp.utils.NetworkResult
import com.example.mantenimientoapp.utils.safeApiCall
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import java.util.Calendar
import javax.inject.Inject

data class GenerarState(val loading: Boolean = false, val result: GenerarOrdenesResultDto? = null, val error: String? = null)

@HiltViewModel
class GenerarOrdenesViewModel @Inject constructor(private val api: ApiService) : ViewModel() {
    private val _state = MutableStateFlow(GenerarState())
    val state: StateFlow<GenerarState> = _state.asStateFlow()

    fun generar(mes: Int, anio: Int) {
        viewModelScope.launch {
            _state.value = GenerarState(loading = true)
            when (val r = safeApiCall { api.generarOrdenes(GenerarOrdenesRequestDto(mes, anio)) }) {
                is NetworkResult.Success -> _state.value = GenerarState(result = r.data)
                is NetworkResult.Error -> _state.value = GenerarState(error = r.message)
                else -> {}
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun GenerarOrdenesScreen(onBack: () -> Unit, vm: GenerarOrdenesViewModel = hiltViewModel()) {
    val state by vm.state.collectAsState()
    val cal = Calendar.getInstance()
    var mes by remember { mutableStateOf(cal.get(Calendar.MONTH) + 1) }
    var anio by remember { mutableStateOf(cal.get(Calendar.YEAR)) }
    var expandedMes by remember { mutableStateOf(false) }

    val meses = listOf("Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre")

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Generar órdenes preventivas") },
                navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, null) } }
            )
        }
    ) { padding ->
        Column(Modifier.padding(padding).padding(16.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
            Text("Genera órdenes PREVENTIVO para los programas que vencen en el mes seleccionado. No duplica existentes.", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)

            ExposedDropdownMenuBox(expanded = expandedMes, onExpandedChange = { expandedMes = it }) {
                OutlinedTextField(
                    value = meses[mes - 1], onValueChange = {}, readOnly = true,
                    label = { Text("Mes") },
                    trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expandedMes) },
                    modifier = Modifier.menuAnchor().fillMaxWidth()
                )
                ExposedDropdownMenu(expanded = expandedMes, onDismissRequest = { expandedMes = false }) {
                    meses.forEachIndexed { i, nombre ->
                        DropdownMenuItem(text = { Text(nombre) }, onClick = { mes = i + 1; expandedMes = false })
                    }
                }
            }

            OutlinedTextField(value = "$anio", onValueChange = { anio = it.toIntOrNull() ?: anio }, label = { Text("Año") }, modifier = Modifier.fillMaxWidth())

            Button(onClick = { vm.generar(mes, anio) }, enabled = !state.loading, modifier = Modifier.fillMaxWidth()) {
                if (state.loading) { CircularProgressIndicator(Modifier.size(16.dp), strokeWidth = 2.dp); Spacer(Modifier.width(8.dp)) }
                Text("Generar órdenes")
            }

            state.result?.let { r ->
                Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)) {
                    Column(Modifier.padding(14.dp)) {
                        Text("${r.creadas} orden(es) creada(s), ${r.existentes} ya existían.", style = MaterialTheme.typography.bodyMedium)
                        if (r.ordenes.isNotEmpty()) Text("IDs: ${r.ordenes.joinToString()}", style = MaterialTheme.typography.bodySmall)
                    }
                }
            }

            state.error?.let { Text(it, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall) }
        }
    }
}
