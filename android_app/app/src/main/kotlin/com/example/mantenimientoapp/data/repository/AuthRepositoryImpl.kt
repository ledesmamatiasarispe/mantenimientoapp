package com.example.mantenimientoapp.data.repository

import com.example.mantenimientoapp.data.preferences.SessionManager
import com.example.mantenimientoapp.data.remote.ApiService
import com.example.mantenimientoapp.data.remote.dto.LoginRequestDto
import com.example.mantenimientoapp.data.remote.dto.TecnicoPublicDto
import com.example.mantenimientoapp.domain.repository.AuthRepository
import com.example.mantenimientoapp.utils.NetworkResult
import com.example.mantenimientoapp.utils.safeApiCall
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject

class AuthRepositoryImpl @Inject constructor(
    private val api: ApiService,
    private val session: SessionManager
) : AuthRepository {

    override suspend fun login(legajo: String, password: String): NetworkResult<TecnicoPublicDto> {
        val result = safeApiCall { api.login(LoginRequestDto(legajo, password)) }
        if (result is NetworkResult.Success) {
            val r = result.data
            session.saveSession(
                token = r.accessToken,
                id = r.tecnico.id,
                nombre = r.tecnico.nombre,
                apellido = r.tecnico.apellido,
                legajo = r.tecnico.legajo,
                esAdmin = r.tecnico.esAdmin
            )
            return NetworkResult.Success(r.tecnico)
        }
        return result as NetworkResult.Error
    }

    override fun isLoggedIn(): Flow<Boolean> = session.isLoggedIn
    override fun esAdmin(): Flow<Boolean> = session.esAdmin
    override fun tecnicoNombre(): Flow<String> = session.tecnicoNombre
    override fun tecnicoId(): Flow<Int> = session.tecnicoId

    override suspend fun logout() = session.clearSession()
}
