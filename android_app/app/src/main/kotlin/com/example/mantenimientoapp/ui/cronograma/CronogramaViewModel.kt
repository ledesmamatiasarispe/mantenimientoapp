package com.example.mantenimientoapp.ui.cronograma

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.mantenimientoapp.data.remote.dto.CronogramaFilaDto
import com.example.mantenimientoapp.domain.repository.BibliotecaRepository
import com.example.mantenimientoapp.utils.NetworkResult
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

data class CronogramaUiState(
    val loading: Boolean = false,
    val error: String? = null,
    val filas: List<CronogramaFilaDto> = emptyList()
)

@HiltViewModel
class CronogramaViewModel @Inject constructor(
    private val repo: BibliotecaRepository
) : ViewModel() {

    private val _state = MutableStateFlow(CronogramaUiState())
    val state: StateFlow<CronogramaUiState> = _state.asStateFlow()

    fun load(anio: Int) {
        viewModelScope.launch {
            _state.value = CronogramaUiState(loading = true)
            when (val r = repo.getCronograma(anio)) {
                is NetworkResult.Success -> _state.value = CronogramaUiState(filas = r.data)
                is NetworkResult.Error -> _state.value = CronogramaUiState(error = r.message)
                else -> {}
            }
        }
    }
}
