package com.example.mantenimientoapp.data.preferences

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.*
import androidx.datastore.preferences.preferencesDataStore
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "session")

data class ServerIpInfo(val ip: String, val label: String, val url: String)

@Singleton
class SessionManager @Inject constructor(
    @ApplicationContext private val context: Context
) {
    companion object {
        val KEY_TOKEN = stringPreferencesKey("token")
        val KEY_TECNICO_ID = intPreferencesKey("tecnico_id")
        val KEY_TECNICO_NOMBRE = stringPreferencesKey("tecnico_nombre")
        val KEY_TECNICO_APELLIDO = stringPreferencesKey("tecnico_apellido")
        val KEY_TECNICO_LEGAJO = stringPreferencesKey("tecnico_legajo")
        val KEY_ES_ADMIN = booleanPreferencesKey("es_admin")
        val KEY_BASE_URL = stringPreferencesKey("base_url")
        val KEY_SERVER_IPS = stringPreferencesKey("server_ips")
    }

    val token: Flow<String?> = context.dataStore.data.map { it[KEY_TOKEN] }
    val isLoggedIn: Flow<Boolean> = context.dataStore.data.map { it[KEY_TOKEN] != null }
    val esAdmin: Flow<Boolean> = context.dataStore.data.map { it[KEY_ES_ADMIN] ?: false }
    val tecnicoId: Flow<Int> = context.dataStore.data.map { it[KEY_TECNICO_ID] ?: 0 }
    val tecnicoNombre: Flow<String> = context.dataStore.data.map {
        val n = it[KEY_TECNICO_NOMBRE] ?: ""
        val a = it[KEY_TECNICO_APELLIDO] ?: ""
        "$n $a".trim()
    }
    val baseUrl: Flow<String> = context.dataStore.data.map {
        it[KEY_BASE_URL] ?: "http://192.168.100.228:50502"
    }
    val serverIps: Flow<List<ServerIpInfo>> = context.dataStore.data.map { prefs ->
        val json = prefs[KEY_SERVER_IPS] ?: return@map emptyList()
        try {
            val type = object : TypeToken<List<ServerIpInfo>>() {}.type
            Gson().fromJson<List<ServerIpInfo>>(json, type) ?: emptyList()
        } catch (_: Exception) { emptyList() }
    }

    suspend fun saveSession(
        token: String, id: Int, nombre: String, apellido: String,
        legajo: String, esAdmin: Boolean
    ) {
        context.dataStore.edit { prefs ->
            prefs[KEY_TOKEN] = token
            prefs[KEY_TECNICO_ID] = id
            prefs[KEY_TECNICO_NOMBRE] = nombre
            prefs[KEY_TECNICO_APELLIDO] = apellido
            prefs[KEY_TECNICO_LEGAJO] = legajo
            prefs[KEY_ES_ADMIN] = esAdmin
        }
    }

    suspend fun clearSession() {
        context.dataStore.edit { prefs ->
            prefs.remove(KEY_TOKEN)
            prefs.remove(KEY_TECNICO_ID)
            prefs.remove(KEY_TECNICO_NOMBRE)
            prefs.remove(KEY_TECNICO_APELLIDO)
            prefs.remove(KEY_TECNICO_LEGAJO)
            prefs.remove(KEY_ES_ADMIN)
        }
    }

    suspend fun saveBaseUrl(url: String) {
        context.dataStore.edit { prefs ->
            prefs[KEY_BASE_URL] = url.trimEnd('/')
        }
    }

    suspend fun saveServerIps(ips: List<ServerIpInfo>) {
        context.dataStore.edit { prefs ->
            prefs[KEY_SERVER_IPS] = Gson().toJson(ips)
        }
    }
}
