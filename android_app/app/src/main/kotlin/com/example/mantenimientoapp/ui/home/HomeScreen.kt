package com.example.mantenimientoapp.ui.home

import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.hilt.navigation.compose.hiltViewModel
import com.example.mantenimientoapp.domain.repository.AuthRepository
import com.example.mantenimientoapp.ui.admin.AdminScreen
import com.example.mantenimientoapp.ui.cronograma.CronogramaScreen
import com.example.mantenimientoapp.ui.ordenes.OrdenesScreen
import com.example.mantenimientoapp.ui.settings.SettingsScreen
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.launch
import javax.inject.Inject
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.stateIn

@HiltViewModel
class HomeViewModel @Inject constructor(
    private val authRepository: AuthRepository
) : ViewModel() {
    val esAdmin = authRepository.esAdmin()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), false)
    val nombre = authRepository.tecnicoNombre()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), "")

    fun logout(scope: kotlinx.coroutines.CoroutineScope, onDone: () -> Unit) {
        scope.launch { authRepository.logout(); onDone() }
    }
}

private sealed class BottomTab(val route: String, val label: String, val icon: ImageVector) {
    object Ordenes : BottomTab("ordenes", "Órdenes", Icons.Default.Assignment)
    object Cronograma : BottomTab("cronograma", "Cronograma", Icons.Default.CalendarMonth)
    object Admin : BottomTab("admin", "Admin", Icons.Default.AdminPanelSettings)
    object Settings : BottomTab("settings", "Ajustes", Icons.Default.Settings)
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    onOrdenClick: (Int) -> Unit,
    onNavigateToAdminEquipos: () -> Unit,
    onNavigateToAdminProgramas: () -> Unit,
    onNavigateToAdminRepuestos: () -> Unit,
    onNavigateToAdminTecnicos: () -> Unit,
    onLogout: () -> Unit,
    vm: HomeViewModel = hiltViewModel()
) {
    val esAdmin by vm.esAdmin.collectAsState()
    val nombre by vm.nombre.collectAsState()
    val scope = rememberCoroutineScope()

    val tabs = remember(esAdmin) {
        buildList {
            add(BottomTab.Ordenes)
            add(BottomTab.Cronograma)
            if (esAdmin) add(BottomTab.Admin)
            add(BottomTab.Settings)
        }
    }

    var selectedTab by remember { mutableStateOf(0) }
    // Reset if admin tab removed after logout
    if (selectedTab >= tabs.size) selectedTab = 0

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(tabs.getOrNull(selectedTab)?.label ?: "Mantenimiento") },
                actions = {
                    if (nombre.isNotBlank()) {
                        Text(nombre, style = MaterialTheme.typography.labelSmall, modifier = Modifier.padding(end = 8.dp))
                    }
                }
            )
        },
        bottomBar = {
            NavigationBar {
                tabs.forEachIndexed { index, tab ->
                    NavigationBarItem(
                        selected = selectedTab == index,
                        onClick = { selectedTab = index },
                        icon = { Icon(tab.icon, contentDescription = tab.label) },
                        label = { Text(tab.label) }
                    )
                }
            }
        }
    ) { innerPadding ->
        val mod = Modifier.padding(innerPadding)
        when (tabs.getOrNull(selectedTab)) {
            BottomTab.Ordenes -> OrdenesScreen(onOrdenClick = onOrdenClick, modifier = mod)
            BottomTab.Cronograma -> CronogramaScreen(modifier = mod)
            BottomTab.Admin -> AdminScreen(
                modifier = mod,
                onEquipos = onNavigateToAdminEquipos,
                onProgramas = onNavigateToAdminProgramas,
                onRepuestos = onNavigateToAdminRepuestos,
                onTecnicos = onNavigateToAdminTecnicos
            )
            BottomTab.Settings -> SettingsScreen(
                modifier = mod,
                onLogout = { vm.logout(scope, onLogout) }
            )
            null -> {}
        }
    }
}
