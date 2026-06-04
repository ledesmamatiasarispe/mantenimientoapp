package com.example.mantenimientoapp.ui.admin

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.mantenimientoapp.data.remote.dto.*
import com.example.mantenimientoapp.domain.repository.AdminRepository
import com.example.mantenimientoapp.domain.repository.BibliotecaRepository
import com.example.mantenimientoapp.utils.NetworkResult
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

// ── Equipos ───────────────────────────────────────────────────────────────────

data class EquiposAdminState(
    val loading: Boolean = true,
    val error: String? = null,
    val equipos: List<AdminEquipoItemDto> = emptyList(),
    val tipos: List<TipoEquipoItemDto> = emptyList(),
    val actionMsg: String? = null
)

@HiltViewModel
class EquiposAdminViewModel @Inject constructor(
    private val admin: AdminRepository
) : ViewModel() {
    private val _state = MutableStateFlow(EquiposAdminState())
    val state: StateFlow<EquiposAdminState> = _state.asStateFlow()

    init { load() }

    fun load() {
        viewModelScope.launch {
            _state.value = _state.value.copy(loading = true, error = null)
            val eq = admin.getEquiposAdmin()
            val tipos = admin.getTiposEquipo()
            if (eq is NetworkResult.Success && tipos is NetworkResult.Success) {
                _state.value = EquiposAdminState(loading = false, equipos = eq.data, tipos = tipos.data)
            } else {
                _state.value = EquiposAdminState(loading = false, error = (eq as? NetworkResult.Error)?.message ?: "Error")
            }
        }
    }

    fun crear(req: AdminEquipoRequestDto, onDone: (Boolean, String?) -> Unit) {
        viewModelScope.launch {
            when (val r = admin.crearEquipo(req)) {
                is NetworkResult.Success -> { load(); onDone(true, null) }
                is NetworkResult.Error -> onDone(false, r.message)
                else -> {}
            }
        }
    }

    fun actualizar(id: Int, req: AdminEquipoRequestDto, onDone: (Boolean, String?) -> Unit) {
        viewModelScope.launch {
            when (val r = admin.actualizarEquipo(id, req)) {
                is NetworkResult.Success -> { load(); onDone(true, null) }
                is NetworkResult.Error -> onDone(false, r.message)
                else -> {}
            }
        }
    }

    fun eliminar(id: Int) {
        viewModelScope.launch {
            when (val r = admin.eliminarEquipo(id)) {
                is NetworkResult.Success -> { load(); _state.value = _state.value.copy(actionMsg = "Equipo eliminado") }
                is NetworkResult.Error -> _state.value = _state.value.copy(actionMsg = r.message)
                else -> {}
            }
        }
    }

    fun clearMsg() { _state.value = _state.value.copy(actionMsg = null) }
}

// ── Programas ─────────────────────────────────────────────────────────────────

data class ProgramasAdminState(
    val loading: Boolean = true,
    val error: String? = null,
    val programas: List<AdminProgramaItemDto> = emptyList(),
    val equipos: List<EquipoCardDto> = emptyList(),
    val actionMsg: String? = null
)

@HiltViewModel
class ProgramasAdminViewModel @Inject constructor(
    private val admin: AdminRepository,
    private val biblioteca: BibliotecaRepository
) : ViewModel() {
    private val _state = MutableStateFlow(ProgramasAdminState())
    val state: StateFlow<ProgramasAdminState> = _state.asStateFlow()

    init { load() }

    fun load() {
        viewModelScope.launch {
            _state.value = _state.value.copy(loading = true, error = null)
            val prog = admin.getProgramasAdmin()
            val eq = biblioteca.getEquipos()
            if (prog is NetworkResult.Success) {
                _state.value = ProgramasAdminState(
                    loading = false,
                    programas = prog.data,
                    equipos = (eq as? NetworkResult.Success)?.data ?: emptyList()
                )
            } else {
                _state.value = ProgramasAdminState(loading = false, error = (prog as? NetworkResult.Error)?.message)
            }
        }
    }

    fun crear(req: AdminProgramaRequestDto, onDone: (Boolean, String?) -> Unit) {
        viewModelScope.launch {
            when (val r = admin.crearPrograma(req)) {
                is NetworkResult.Success -> { load(); onDone(true, null) }
                is NetworkResult.Error -> onDone(false, r.message)
                else -> {}
            }
        }
    }

    fun actualizar(id: Int, req: AdminProgramaRequestDto, onDone: (Boolean, String?) -> Unit) {
        viewModelScope.launch {
            when (val r = admin.actualizarPrograma(id, req)) {
                is NetworkResult.Success -> { load(); onDone(true, null) }
                is NetworkResult.Error -> onDone(false, r.message)
                else -> {}
            }
        }
    }

    fun eliminar(id: Int) {
        viewModelScope.launch {
            when (val r = admin.eliminarPrograma(id)) {
                is NetworkResult.Success -> { load(); _state.value = _state.value.copy(actionMsg = "Programa eliminado") }
                is NetworkResult.Error -> _state.value = _state.value.copy(actionMsg = r.message)
                else -> {}
            }
        }
    }

    fun clearMsg() { _state.value = _state.value.copy(actionMsg = null) }
}

// ── Repuestos ─────────────────────────────────────────────────────────────────

data class RepuestosAdminState(
    val loading: Boolean = true,
    val error: String? = null,
    val repuestos: List<AdminRepuestoItemDto> = emptyList(),
    val actionMsg: String? = null
)

@HiltViewModel
class RepuestosAdminViewModel @Inject constructor(
    private val admin: AdminRepository
) : ViewModel() {
    private val _state = MutableStateFlow(RepuestosAdminState())
    val state: StateFlow<RepuestosAdminState> = _state.asStateFlow()

    init { load() }

    fun load() {
        viewModelScope.launch {
            _state.value = _state.value.copy(loading = true, error = null)
            when (val r = admin.getRepuestosAdmin()) {
                is NetworkResult.Success -> _state.value = RepuestosAdminState(loading = false, repuestos = r.data)
                is NetworkResult.Error -> _state.value = RepuestosAdminState(loading = false, error = r.message)
                else -> {}
            }
        }
    }

    fun crear(req: AdminRepuestoRequestDto, onDone: (Boolean, String?) -> Unit) {
        viewModelScope.launch {
            when (val r = admin.crearRepuesto(req)) {
                is NetworkResult.Success -> { load(); onDone(true, null) }
                is NetworkResult.Error -> onDone(false, r.message)
                else -> {}
            }
        }
    }

    fun actualizar(id: Int, req: AdminRepuestoRequestDto, onDone: (Boolean, String?) -> Unit) {
        viewModelScope.launch {
            when (val r = admin.actualizarRepuesto(id, req)) {
                is NetworkResult.Success -> { load(); onDone(true, null) }
                is NetworkResult.Error -> onDone(false, r.message)
                else -> {}
            }
        }
    }

    fun eliminar(id: Int) {
        viewModelScope.launch {
            when (val r = admin.eliminarRepuesto(id)) {
                is NetworkResult.Success -> { load(); _state.value = _state.value.copy(actionMsg = "Repuesto eliminado") }
                is NetworkResult.Error -> _state.value = _state.value.copy(actionMsg = r.message)
                else -> {}
            }
        }
    }

    fun clearMsg() { _state.value = _state.value.copy(actionMsg = null) }
}

// ── Técnicos ──────────────────────────────────────────────────────────────────

data class TecnicosAdminState(
    val loading: Boolean = true,
    val error: String? = null,
    val tecnicos: List<AdminTecnicoItemDto> = emptyList(),
    val actionMsg: String? = null
)

@HiltViewModel
class TecnicosAdminViewModel @Inject constructor(
    private val admin: AdminRepository
) : ViewModel() {
    private val _state = MutableStateFlow(TecnicosAdminState())
    val state: StateFlow<TecnicosAdminState> = _state.asStateFlow()

    init { load() }

    fun load() {
        viewModelScope.launch {
            _state.value = _state.value.copy(loading = true, error = null)
            when (val r = admin.getTecnicosAdmin()) {
                is NetworkResult.Success -> _state.value = TecnicosAdminState(loading = false, tecnicos = r.data)
                is NetworkResult.Error -> _state.value = TecnicosAdminState(loading = false, error = r.message)
                else -> {}
            }
        }
    }

    fun crear(req: AdminTecnicoCreateDto, onDone: (Boolean, String?) -> Unit) {
        viewModelScope.launch {
            when (val r = admin.crearTecnico(req)) {
                is NetworkResult.Success -> { load(); onDone(true, null) }
                is NetworkResult.Error -> onDone(false, r.message)
                else -> {}
            }
        }
    }

    fun actualizar(id: Int, req: AdminTecnicoUpdateDto, onDone: (Boolean, String?) -> Unit) {
        viewModelScope.launch {
            when (val r = admin.actualizarTecnico(id, req)) {
                is NetworkResult.Success -> { load(); onDone(true, null) }
                is NetworkResult.Error -> onDone(false, r.message)
                else -> {}
            }
        }
    }

    fun setPassword(id: Int, password: String, onDone: (Boolean, String?) -> Unit) {
        viewModelScope.launch {
            when (val r = admin.setPassword(id, password)) {
                is NetworkResult.Success -> onDone(true, null)
                is NetworkResult.Error -> onDone(false, r.message)
                else -> {}
            }
        }
    }

    fun eliminar(id: Int) {
        viewModelScope.launch {
            when (val r = admin.eliminarTecnico(id)) {
                is NetworkResult.Success -> { load(); _state.value = _state.value.copy(actionMsg = "Técnico eliminado") }
                is NetworkResult.Error -> _state.value = _state.value.copy(actionMsg = r.message)
                else -> {}
            }
        }
    }

    fun clearMsg() { _state.value = _state.value.copy(actionMsg = null) }
}
