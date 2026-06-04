package com.example.mantenimientoapp.data.remote.dto

import com.google.gson.annotations.SerializedName

data class CronogramaFilaDto(
    @SerializedName("programa_id") val programaId: Int,
    @SerializedName("equipo_id") val equipoId: Int,
    @SerializedName("equipo_nombre") val equipoNombre: String,
    val etiqueta: String,
    val meses: Map<String, String>
)
