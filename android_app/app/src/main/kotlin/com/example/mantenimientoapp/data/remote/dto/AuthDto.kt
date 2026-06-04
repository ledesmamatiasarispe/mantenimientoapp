package com.example.mantenimientoapp.data.remote.dto

import com.google.gson.annotations.SerializedName

data class LoginRequestDto(
    val legajo: String,
    val password: String
)

data class TecnicoPublicDto(
    val id: Int,
    val nombre: String,
    val apellido: String,
    val legajo: String,
    val telefono: String,
    val especialidad: String,
    @SerializedName("es_admin") val esAdmin: Boolean = false
)

data class TokenResponseDto(
    @SerializedName("access_token") val accessToken: String,
    @SerializedName("token_type") val tokenType: String,
    val tecnico: TecnicoPublicDto
)
