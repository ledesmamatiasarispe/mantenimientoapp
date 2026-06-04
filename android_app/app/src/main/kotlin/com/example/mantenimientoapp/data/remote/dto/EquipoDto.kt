package com.example.mantenimientoapp.data.remote.dto

import com.google.gson.annotations.SerializedName

data class EquipoCardDto(
    val id: Int,
    val nombre: String,
    @SerializedName("tipo_id") val tipoId: Int?,
    @SerializedName("tipo_nombre") val tipoNombre: String,
    @SerializedName("numero_serie") val numeroSerie: String,
    val marca: String,
    val modelo: String,
    val ubicacion: String,
    val observaciones: String,
    @SerializedName("programas_activos_count") val programasActivosCount: Int
)

data class RepuestoDisponibleDto(
    val id: Int,
    val nombre: String,
    @SerializedName("stock_actual") val stockActual: Double,
    @SerializedName("stock_minimo") val stockMinimo: Double
)
