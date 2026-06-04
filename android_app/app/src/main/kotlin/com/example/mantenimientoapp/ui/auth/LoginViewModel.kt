package com.example.mantenimientoapp.ui.auth

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.mantenimientoapp.domain.repository.AuthRepository
import com.example.mantenimientoapp.utils.NetworkResult
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class LoginUiState(
    val loading: Boolean = false,
    val error: String? = null,
    val success: Boolean = false
)

@HiltViewModel
class LoginViewModel @Inject constructor(
    private val authRepository: AuthRepository
) : ViewModel() {

    val isLoggedIn = authRepository.isLoggedIn()

    private val _uiState = MutableStateFlow(LoginUiState())
    val uiState: StateFlow<LoginUiState> = _uiState.asStateFlow()

    fun login(legajo: String, password: String) {
        if (legajo.isBlank() || password.isBlank()) {
            _uiState.value = LoginUiState(error = "Ingrese legajo y contraseña")
            return
        }
        viewModelScope.launch {
            _uiState.value = LoginUiState(loading = true)
            when (val r = authRepository.login(legajo.trim(), password)) {
                is NetworkResult.Success -> _uiState.value = LoginUiState(success = true)
                is NetworkResult.Error -> _uiState.value = LoginUiState(error = r.message)
                else -> {}
            }
        }
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }
}
