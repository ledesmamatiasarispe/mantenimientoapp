package com.example.mantenimientoapp.ui.servercheck

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.mantenimientoapp.data.preferences.ServerIpInfo
import com.example.mantenimientoapp.data.preferences.SessionManager
import com.example.mantenimientoapp.data.remote.ApiService
import com.example.mantenimientoapp.domain.repository.AuthRepository
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import java.util.concurrent.TimeUnit
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

    val serverIps: StateFlow<List<ServerIpInfo>> = session.serverIps
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    // Cliente HTTP ligero con timeout corto solo para el health check
    private val pingClient = OkHttpClient.Builder()
        .connectTimeout(5, TimeUnit.SECONDS)
        .readTimeout(5, TimeUnit.SECONDS)
        .callTimeout(6, TimeUnit.SECONDS)
        .build()

    init { check() }

    fun check() {
        viewModelScope.launch {
            _state.value = ServerState.Checking
            val url = session.baseUrl.first().trimEnd('/')
            val ok = withContext(Dispatchers.IO) { ping(url) }
            if (ok) {
                fetchAndCacheNetworkInfo()
                _state.value = ServerState.Connected
            } else {
                _state.value = ServerState.Failed(
                    url = url,
                    error = "No se pudo conectar a $url"
                )
            }
        }
    }

    fun saveUrlAndCheck(url: String) {
        viewModelScope.launch {
            session.saveBaseUrl(url.trimEnd('/'))
            check()
        }
    }

    private fun ping(baseUrl: String): Boolean {
        return try {
            val request = Request.Builder().url("$baseUrl/api/health").build()
            pingClient.newCall(request).execute().use { it.isSuccessful }
        } catch (_: Exception) { false }
    }

    private suspend fun fetchAndCacheNetworkInfo() {
        try {
            val url = session.baseUrl.first().trimEnd('/')
            val request = Request.Builder().url("$url/api/network-info").build()
            val body = withContext(Dispatchers.IO) {
                pingClient.newCall(request).execute().use { it.body?.string() }
            } ?: return

            // Parsear manualmente para no depender del ApiService (que tiene otra baseUrl)
            val type = object : TypeToken<NetworkInfoResponse>() {}.type
            val info: NetworkInfoResponse = Gson().fromJson(body, type)
            val ips = info.ips.map { ServerIpInfo(ip = it.ip, label = it.label, url = "http://${it.ip}:${info.port}") }
            session.saveServerIps(ips)
        } catch (_: Exception) { }
    }

    // Data classes locales solo para parsear la respuesta
    private data class NetworkInfoResponse(val port: Int, val ips: List<IpEntry>)
    private data class IpEntry(val ip: String, val label: String)
}
