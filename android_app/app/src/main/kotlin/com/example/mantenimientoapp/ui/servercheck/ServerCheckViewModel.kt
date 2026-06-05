package com.example.mantenimientoapp.ui.servercheck

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.mantenimientoapp.data.preferences.ServerIpInfo
import com.example.mantenimientoapp.data.preferences.SessionManager
import com.example.mantenimientoapp.data.remote.ApiService
import com.example.mantenimientoapp.domain.repository.AuthRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

sealed class ServerState {
    data object Checking : ServerState()
    data object Connected : ServerState()
    data class Failed(val url: String, val error: String) : ServerState()
}

@HiltViewModel
class ServerCheckViewModel @Inject constructor(
    private val api: ApiService,
    private val session: SessionManager,
    private val auth: AuthRepository
) : ViewModel() {

    private val _state = MutableStateFlow<ServerState>(ServerState.Checking)
    val state: StateFlow<ServerState> = _state.asStateFlow()

    val isLoggedIn = auth.isLoggedIn()

    val baseUrl: StateFlow<String> = session.baseUrl
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), "")

    // IPs cacheadas del servidor (de la última conexión exitosa)
    val serverIps: StateFlow<List<ServerIpInfo>> = session.serverIps
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    init { check() }

    fun check() {
        viewModelScope.launch {
            _state.value = ServerState.Checking
            val url = session.baseUrl.first()
            try {
                val r = api.health()
                if (r.isSuccessful || r.code() == 401) {
                    // Aprovechamos la conexión para obtener las IPs del servidor
                    fetchAndCacheNetworkInfo()
                    _state.value = ServerState.Connected
                } else {
                    _state.value = ServerState.Failed(url, "Error ${r.code()}")
                }
            } catch (e: Exception) {
                _state.value = ServerState.Failed(
                    url = url,
                    error = "No se pudo conectar a $url"
                )
            }
        }
    }

    fun saveUrlAndCheck(url: String) {
        viewModelScope.launch {
            session.saveBaseUrl(url)
            check()
        }
    }

    private suspend fun fetchAndCacheNetworkInfo() {
        try {
            val info = api.networkInfo()
            val ips = info.ips.map { dto ->
                ServerIpInfo(
                    ip = dto.ip,
                    label = dto.label,
                    url = "http://${dto.ip}:${info.port}"
                )
            }
            session.saveServerIps(ips)
        } catch (_: Exception) {
            // No crítico — las IPs cacheadas previas siguen disponibles
        }
    }
}
