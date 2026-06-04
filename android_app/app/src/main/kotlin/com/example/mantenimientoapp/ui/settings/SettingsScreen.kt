package com.example.mantenimientoapp.ui.settings

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel

@Composable
fun SettingsScreen(
    modifier: Modifier = Modifier,
    onLogout: () -> Unit,
    vm: SettingsViewModel = hiltViewModel()
) {
    val baseUrl by vm.baseUrl.collectAsState()
    val nombre by vm.tecnicoNombre.collectAsState()
    val esAdmin by vm.esAdmin.collectAsState()

    var urlInput by remember(baseUrl) { mutableStateOf(baseUrl) }
    var urlSaved by remember { mutableStateOf(false) }

    Column(
        modifier.fillMaxSize().padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Perfil
        Card(modifier = Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    Icon(Icons.Default.Person, contentDescription = null, modifier = Modifier.size(40.dp), tint = MaterialTheme.colorScheme.primary)
                    Column {
                        Text(nombre, style = MaterialTheme.typography.titleMedium)
                        if (esAdmin) {
                            Text("Administrador", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.primary)
                        }
                    }
                }
            }
        }

        // URL del servidor
        Card(modifier = Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text("Servidor API", style = MaterialTheme.typography.titleSmall)
                Text("Ingresá la IP o URL del servidor (ej: http://192.168.0.10:54321)", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)

                OutlinedTextField(
                    value = urlInput,
                    onValueChange = { urlInput = it; urlSaved = false },
                    label = { Text("URL del servidor") },
                    placeholder = { Text("http://192.168.0.x:54321") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )

                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(
                        onClick = {
                            vm.saveBaseUrl(urlInput)
                            urlSaved = true
                        },
                        modifier = Modifier.weight(1f)
                    ) {
                        Icon(Icons.Default.Save, null, Modifier.size(16.dp))
                        Spacer(Modifier.width(4.dp))
                        Text("Guardar")
                    }
                }

                if (urlSaved) {
                    Text("URL guardada correctamente", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.primary)
                }
            }
        }

        // URLs rápidas
        Card(modifier = Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("URLs frecuentes", style = MaterialTheme.typography.titleSmall)
                listOf(
                    "Red local (default)" to "http://192.168.0.1:54321",
                    "PC laboratorio" to "http://LAB01.local:54321",
                    "Emulador Android" to "http://10.0.2.2:54321"
                ).forEach { (label, url) ->
                    OutlinedButton(
                        onClick = { urlInput = url; vm.saveBaseUrl(url); urlSaved = true },
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column {
                            Text(label, style = MaterialTheme.typography.labelMedium)
                            Text(url, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
                        }
                    }
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
