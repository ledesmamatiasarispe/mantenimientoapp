package com.example.mantenimientoapp.ui.servercheck

import androidx.compose.animation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.example.mantenimientoapp.data.preferences.ServerIpInfo

@Composable
fun ServerCheckScreen(
    onConnectedLoggedIn: () -> Unit,
    onConnectedNeedLogin: () -> Unit,
    vm: ServerCheckViewModel = hiltViewModel()
) {
    val state by vm.state.collectAsState()
    val isLoggedIn by vm.isLoggedIn.collectAsState(initial = false)
    val cachedIps by vm.serverIps.collectAsState()

    LaunchedEffect(state) {
        if (state is ServerState.Connected) {
            if (isLoggedIn) onConnectedLoggedIn() else onConnectedNeedLogin()
        }
    }

    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        AnimatedContent(targetState = state, label = "server_check") { serverState ->
            when (serverState) {
                is ServerState.Checking -> CheckingView()
                is ServerState.Failed -> FailedView(
                    currentUrl = serverState.url,
                    error = serverState.error,
                    cachedIps = cachedIps,
                    onRetry = { vm.check() },
                    onSaveUrl = { url -> vm.saveUrlAndCheck(url) }
                )
                is ServerState.Connected -> CheckingView()
            }
        }
    }
}

@Composable
private fun CheckingView() {
    Column(
        Modifier.padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(20.dp)
    ) {
        CircularProgressIndicator(Modifier.size(48.dp))
        Text(
            "Conectando al servidor…",
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.outline
        )
    }
}

@Composable
private fun FailedView(
    currentUrl: String,
    error: String,
    cachedIps: List<ServerIpInfo>,
    onRetry: () -> Unit,
    onSaveUrl: (String) -> Unit
) {
    var urlInput by remember(currentUrl) { mutableStateOf(currentUrl) }

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(24.dp)
    ) {
        Column(
            Modifier
                .padding(24.dp)
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            Icon(
                Icons.Default.WifiOff,
                contentDescription = null,
                modifier = Modifier.size(48.dp).align(Alignment.CenterHorizontally),
                tint = MaterialTheme.colorScheme.error
            )

            Text(
                "Sin conexión al servidor",
                style = MaterialTheme.typography.titleLarge,
                textAlign = TextAlign.Center,
                modifier = Modifier.fillMaxWidth()
            )

            Text(
                error,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.error,
                textAlign = TextAlign.Center,
                modifier = Modifier.fillMaxWidth()
            )

            HorizontalDivider()

            Text(
                "Ingresá la dirección del servidor:",
                style = MaterialTheme.typography.bodyMedium
            )

            OutlinedTextField(
                value = urlInput,
                onValueChange = { urlInput = it },
                label = { Text("URL del servidor") },
                placeholder = { Text("http://192.168.x.x:54321") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                leadingIcon = { Icon(Icons.Default.Dns, null) }
            )

            // IPs del servidor (cacheadas de la última conexión exitosa)
            if (cachedIps.isNotEmpty()) {
                Text(
                    "IPs del servidor (última conexión exitosa):",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.outline
                )
                cachedIps.forEach { info ->
                    IpButton(info = info, onClick = { urlInput = info.url })
                }
            } else {
                Text(
                    "Conectate una vez para que el servidor informe sus IPs automáticamente.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.outline
                )
            }

            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                OutlinedButton(onClick = onRetry, modifier = Modifier.weight(1f)) {
                    Icon(Icons.Default.Refresh, null, Modifier.size(16.dp))
                    Spacer(Modifier.width(4.dp))
                    Text("Reintentar")
                }
                Button(
                    onClick = { onSaveUrl(urlInput) },
                    enabled = urlInput.isNotBlank(),
                    modifier = Modifier.weight(1f)
                ) {
                    Icon(Icons.Default.Check, null, Modifier.size(16.dp))
                    Spacer(Modifier.width(4.dp))
                    Text("Conectar")
                }
            }
        }
    }
}

@Composable
private fun IpButton(info: ServerIpInfo, onClick: () -> Unit) {
    val icon = when {
        info.label.contains("local", ignoreCase = true) -> Icons.Default.Wifi
        info.label.contains("Hamachi", ignoreCase = true) -> Icons.Default.VpnLock
        info.label.contains("pública", ignoreCase = true) -> Icons.Default.Public
        else -> Icons.Default.NetworkCheck
    }
    OutlinedButton(
        onClick = onClick,
        modifier = Modifier.fillMaxWidth()
    ) {
        Icon(icon, null, Modifier.size(16.dp))
        Spacer(Modifier.width(8.dp))
        Column(Modifier.weight(1f)) {
            Text(info.label, style = MaterialTheme.typography.labelMedium)
            Text(info.url, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
        }
    }
}
