package com.example.mantenimientoapp.ui.ordenes

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.mantenimientoapp.data.preferences.SessionManager
import com.example.mantenimientoapp.data.remote.dto.*
import com.example.mantenimientoapp.domain.repository.BibliotecaRepository
import com.example.mantenimientoapp.domain.repository.OrdenesRepository
import com.example.mantenimientoapp.utils.NetworkResult
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

// ── Lista de órdenes ──────────────────────────────────────────────────────────

data class OrdenesUiState(
    val loading: Boolean = false,
    val error: String? = null,
    val pendientes: List<OrdenCardDto> = emptyList(),
    val mias: List<OrdenCardDto> = emptyList(),
    val todas: List<OrdenCardDto> = emptyList(),
    val completadas: List<OrdenCardDto> = emptyList()
)

@HiltViewModel
class OrdenesViewModel @Inject constructor(
    private val ordenesRepo: OrdenesRepository,
    private val bibliotecaRepo: BibliotecaRepository,
    private val session: SessionManager
) : ViewModel() {

    private val _state = MutableStateFlow(OrdenesUiState(loading = true))
    val state: StateFlow<OrdenesUiState> = _state.asStateFlow()

    val tecnicoId: Flow<Int> = session.tecnicoId

    // Equipos y repuestos para formulario de nueva orden
    private val _equipos = MutableStateFlow<List<EquipoCardDto>>(emptyList())
    val equipos: StateFlow<List<EquipoCardDto>> = _equipos.asStateFlow()

    private val _repuestos = MutableStateFlow<List<RepuestoDisponibleDto>>(emptyList())
    val repuestos: StateFlow<List<RepuestoDisponibleDto>> = _repuestos.asStateFlow()

    init { loadAll() }

    fun loadAll() {
        viewModelScope.launch {
            _state.value = _state.value.copy(loading = true, error = null)

            val tid = session.tecnicoId.first()

            val todasRes = ordenesRepo.getOrdenes()
            if (todasRes is NetworkResult.Error) {
                _state.value = OrdenesUiState(loading = false, error = todasRes.message)
                return@launch
            }
            val todas = (todasRes as NetworkResult.Success).data

            _state.value = OrdenesUiState(
                loading = false,
                pendientes = todas.filter { it.estado == "PENDIENTE" },
                mias = todas.filter { it.tecnicoId == tid || it.colaboradores(tid) },
                todas = todas,
                completadas = todas.filter { it.estado == "COMPLETADA" }
            )

            // Cargar en background para formularios
            launch {
                val eq = bibliotecaRepo.getEquipos()
                if (eq is NetworkResult.Success) _equipos.value = eq.data
            }
            launch {
                val rep = bibliotecaRepo.getRepuestos()
                if (rep is NetworkResult.Success) _repuestos.value = rep.data
            }
        }
    }

    fun crearOrden(equipoId: Int, tipo: String, descripcion: String, observaciones: String, onDone: (Boolean, String?) -> Unit) {
        viewModelScope.launch {
            when (val r = ordenesRepo.crearOrden(equipoId, tipo, descripcion, observaciones)) {
                is NetworkResult.Success -> { loadAll(); onDone(true, null) }
                is NetworkResult.Error -> onDone(false, r.message)
                else -> {}
            }
        }
    }
}

// Extension para check colaboradores (no tenemos el campo en OrdenCard, usamos solo tecnicoId)
private fun OrdenCardDto.colaboradores(tid: Int) = tecnicoId == tid

// ── Detalle de orden ──────────────────────────────────────────────────────────

data class OrdenDetailUiState(
    val loading: Boolean = true,
    val error: String? = null,
    val orden: OrdenDetailDto? = null,
    val actionLoading: Boolean = false,
    val actionError: String? = null,
    val actionSuccess: String? = null
)

@HiltViewModel
class OrdenDetailViewModel @Inject constructor(
    private val ordenesRepo: OrdenesRepository,
    private val bibliotecaRepo: BibliotecaRepository,
    private val session: SessionManager
) : ViewModel() {

    private val _state = MutableStateFlow(OrdenDetailUiState())
    val state: StateFlow<OrdenDetailUiState> = _state.asStateFlow()

    val tecnicoId: Flow<Int> = session.tecnicoId
    val baseUrl: Flow<String> = session.baseUrl
    val token: Flow<String?> = session.token

    private val _repuestos = MutableStateFlow<List<RepuestoDisponibleDto>>(emptyList())
    val repuestos: StateFlow<List<RepuestoDisponibleDto>> = _repuestos.asStateFlow()

    fun load(ordenId: Int) {
        viewModelScope.launch {
            _state.value = OrdenDetailUiState(loading = true)
            when (val r = ordenesRepo.getOrden(ordenId)) {
                is NetworkResult.Success -> {
                    _state.value = OrdenDetailUiState(loading = false, orden = r.data)
                    launch {
                        val rep = bibliotecaRepo.getRepuestos()
                        if (rep is NetworkResult.Success) _repuestos.value = rep.data
                    }
                }
                is NetworkResult.Error -> _state.value = OrdenDetailUiState(loading = false, error = r.message)
                else -> {}
            }
        }
    }

    private fun action(block: suspend () -> NetworkResult<Unit>, successMsg: String) {
        val ordenId = _state.value.orden?.id ?: return
        viewModelScope.launch {
            _state.value = _state.value.copy(actionLoading = true, actionError = null, actionSuccess = null)
            when (val r = block()) {
                is NetworkResult.Success -> {
                    _state.value = _state.value.copy(actionLoading = false, actionSuccess = successMsg)
                    load(ordenId)
                }
                is NetworkResult.Error -> _state.value = _state.value.copy(actionLoading = false, actionError = r.message)
                else -> {}
            }
        }
    }

    fun aceptar() = action({ ordenesRepo.aceptarOrden(_state.value.orden!!.id) }, "Te uniste a la orden")
    fun cancelarAceptacion() = action({ ordenesRepo.cancelarAceptacion(_state.value.orden!!.id) }, "Aceptación cancelada")
    fun completar(obs: String) = action({ ordenesRepo.completarOrden(_state.value.orden!!.id, obs) }, "Orden completada")
    fun togglePaso(pasoId: Int) = action({ ordenesRepo.togglePaso(_state.value.orden!!.id, pasoId) }, "")
    fun eliminarFoto(fotoId: Int) = action({ ordenesRepo.eliminarFoto(_state.value.orden!!.id, fotoId) }, "Foto eliminada")

    fun agregarRepuesto(repuestoId: Int, cantidad: Double, onDone: (Boolean, String?) -> Unit) {
        val ordenId = _state.value.orden?.id ?: return
        viewModelScope.launch {
            when (val r = ordenesRepo.agregarRepuesto(ordenId, repuestoId, cantidad)) {
                is NetworkResult.Success -> { load(ordenId); onDone(true, null) }
                is NetworkResult.Error -> onDone(false, r.message)
                else -> {}
            }
        }
    }

    fun quitarRepuesto(itemId: Int) {
        val ordenId = _state.value.orden?.id ?: return
        action({ ordenesRepo.quitarRepuesto(ordenId, itemId) }, "Repuesto quitado")
    }

    fun agregarObservacion(texto: String, onDone: (Boolean, String?) -> Unit) {
        val ordenId = _state.value.orden?.id ?: return
        viewModelScope.launch {
            when (val r = ordenesRepo.agregarObservacion(ordenId, texto)) {
                is NetworkResult.Success -> { load(ordenId); onDone(true, null) }
                is NetworkResult.Error -> onDone(false, r.message)
                else -> {}
            }
        }
    }

    fun clearMessages() {
        _state.value = _state.value.copy(actionError = null, actionSuccess = null)
    }

    fun getFotoUrl(ordenId: Int, fotoId: Int): String {
        val base = runBlocking { session.baseUrl.first() }
        val tok = runBlocking { session.token.first() } ?: ""
        return ordenesRepo.getFotoUrl(base, ordenId, fotoId, tok)
    }
}

private fun <T> runBlocking(block: suspend () -> T): T =
    kotlinx.coroutines.runBlocking { block() }
