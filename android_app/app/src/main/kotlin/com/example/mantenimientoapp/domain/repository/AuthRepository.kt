package com.example.mantenimientoapp.domain.repository

import com.example.mantenimientoapp.data.remote.dto.TecnicoPublicDto
import com.example.mantenimientoapp.utils.NetworkResult
import kotlinx.coroutines.flow.Flow

interface AuthRepository {
    suspend fun login(legajo: String, password: String): NetworkResult<TecnicoPublicDto>
    fun isLoggedIn(): Flow<Boolean>
    fun esAdmin(): Flow<Boolean>
    fun tecnicoNombre(): Flow<String>
    fun tecnicoId(): Flow<Int>
    suspend fun logout()
}
