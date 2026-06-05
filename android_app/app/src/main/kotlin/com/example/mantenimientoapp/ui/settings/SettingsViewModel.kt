package com.example.mantenimientoapp.ui.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.mantenimientoapp.data.preferences.ServerIpInfo
import com.example.mantenimientoapp.data.preferences.SessionManager
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val session: SessionManager
) : ViewModel() {

    val baseUrl: StateFlow<String> = session.baseUrl
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), "")

    val tecnicoNombre: StateFlow<String> = session.tecnicoNombre
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), "")

    val esAdmin: StateFlow<Boolean> = session.esAdmin
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), false)

    val serverIps: StateFlow<List<ServerIpInfo>> = session.serverIps
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    fun saveBaseUrl(url: String) {
        viewModelScope.launch { session.saveBaseUrl(url) }
    }
}
