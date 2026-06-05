package com.example.mantenimientoapp.ui.settings

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.example.mantenimientoapp.data.preferences.ServerIpInfo

@Composable
fun SettingsScreen(
    modifier: Modifier = Modifier,
    onLogout: () -> Unit,
    vm: SettingsViewModel = hiltViewModel()
) {
    val baseUrl by vm.baseUrl.collectAsState()
    val nombre by vm.tecnicoNombre.collectAsState()
    val esAdmin by vm.esAdmin.collectAsState()
    val serverIps by vm.serverIps.collectAsState()

    var urlInput by remember(baseUrl) { mutableStateOf(baseUrl) }
    var urlSaved by remember { mutableStateOf(false) }

    Column(
        modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Perfil
        Card(modifier = Modifier.fillMaxWidth()) {
            Row(
                Modifier.padding(16.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Icon(Icons.Default.Person, null, Modifier.size(40.dp), tint = MaterialTheme.colorScheme.primary)
                Column {
                    Text(nombre, style = MaterialTheme.typography.titleMedium)
                    if (esAdmin) {
                        Text("Administrador", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.primary)
                    }
                }
            }
        }

        // IPs del servidor
        if (serverIps.isNotEmpty()) {
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Icon(Icons.Default.Router, null, Modifier.size(20.dp), tint = MaterialTheme.colorScheme.primary)
                        Text("Direcciones del servidor", style = MaterialTheme.typography.titleSmall)
                    }
                    Text(
                        "El servidor es accesible desde estas direcciones:",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.outline
                    )
                    serverIps.forEach { info ->
                        ServerIpRow(info = info, isCurrent = info.url == baseUrl, onSelect = {
                            urlInput = info.url
                            vm.saveBaseUrl(info.url)
                            urlSaved = true
                        })
                    }
                }
            }
        }

        // URL del servidor (campo editable)
        Card(modifier = Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text("URL activa", style = MaterialTheme.typography.titleSmall)
                Text("URL que usa la app para conectarse al servidor.", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)

                OutlinedTextField(
                    value = urlInput,
                    onValueChange = { urlInput = it; urlSaved = false },
                    label = { Text("URL del servidor") },
                    placeholder = { Text("http://192.168.x.x:54321") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )

                Button(
                    onClick = { vm.saveBaseUrl(urlInput); urlSaved = true },
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Icon(Icons.Default.Save, null, Modifier.size(16.dp))
                    Spacer(Modifier.width(4.dp))
                    Text("Guardar URL")
                }

                if (urlSaved) {
                    Text("URL guardada", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.primary)
                }
            }
        }

        Spacer(Modifier.weight(1f))

        // Cerrar sesión
        Button(
            onClick = onLogout,
            colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.error),
            modifier = Modifier.fillMaxWidth()
        ) {
            Icon(Icons.Default.Logout, null, Modifier.size(16.dp))
            Spacer(Modifier.width(8.dp))
            Text("Cerrar sesión")
        }
    }
}

@Composable
private fun ServerIpRow(info: ServerIpInfo, isCurrent: Boolean, onSelect: () -> Unit) {
    val icon = when {
        info.label.contains("local", ignoreCase = true) -> Icons.Default.Wifi
        info.label.contains("Hamachi", ignoreCase = true) -> Icons.Default.VpnLock
        info.label.contains("pública", ignoreCase = true) -> Icons.Default.Public
        else -> Icons.Default.NetworkCheck
    }
    Surface(
        onClick = onSelect,
        shape = MaterialTheme.shapes.small,
        color = if (isCurrent) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.surfaceVariant,
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            Modifier.padding(12.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            Icon(icon, null, Modifier.size(20.dp),
                tint = if (isCurrent) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.outline)
            Column(Modifier.weight(1f)) {
                Text(info.label, style = MaterialTheme.typography.labelMedium)
                Text(info.url, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
            }
            if (isCurrent) {
                Icon(Icons.Default.CheckCircle, "Activa", Modifier.size(16.dp), tint = MaterialTheme.colorScheme.primary)
            }
        }
    }
}
