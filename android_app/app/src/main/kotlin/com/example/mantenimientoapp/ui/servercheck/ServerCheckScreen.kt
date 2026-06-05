package com.example.mantenimientoapp.ui.servercheck

import androidx.compose.animation.*
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel

@Composable
fun ServerCheckScreen(
    onConnectedLoggedIn: () -> Unit,
    onConnectedNeedLogin: () -> Unit,
    vm: ServerCheckViewModel = hiltViewModel()
) {
    val state by vm.state.collectAsState()
    val currentUrl by vm.baseUrl.collectAsState()
    val isLoggedIn by vm.isLoggedIn.collectAsState(initial = false)

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
                    onRetry = { vm.check() },
                    onSaveUrl = { url -> vm.saveUrlAndCheck(url) }
                )
                is ServerState.Connected -> CheckingView() // Transitorio antes de navegar
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
            Modifier.padding(24.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Ícono de error
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
                "Ingresá la dirección IP del servidor:",
                style = MaterialTheme.typography.bodyMedium
            )

            OutlinedTextField(
                value = urlInput,
                onValueChange = { urlInput = it },
                label = { Text("URL del servidor") },
                placeholder = { Text("http://192.168.100.228:54321") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                leadingIcon = { Icon(Icons.Default.Dns, null) }
            )

            // URLs rápidas
            Text("Accesos rápidos:", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.outline)
            listOf(
                "Esta PC" to "http://192.168.100.228:54321",
                "LABOR01 (red local)" to "http://192.168.0.116:54321"
            ).forEach { (label, url) ->
                OutlinedButton(
                    onClick = { urlInput = url },
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text(label, style = MaterialTheme.typography.labelMedium)
                    Spacer(Modifier.width(4.dp))
                    Text(url, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
                }
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
