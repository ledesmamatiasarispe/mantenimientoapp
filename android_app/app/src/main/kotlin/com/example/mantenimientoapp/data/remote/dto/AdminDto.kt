package com.example.mantenimientoapp.data.remote.dto

import com.google.gson.annotations.SerializedName

data class TipoEquipoItemDto(val id: Int, val nombre: String, val activo: Boolean)
data class TipoEquipoRequestDto(val nombre: String, val activo: Boolean = true)

data class AdminEquipoItemDto(
    val id: Int,
    val nombre: String,
    @SerializedName("tipo_id") val tipoId: Int?,
    @SerializedName("tipo_nombre") val tipoNombre: String,
    @SerializedName("numero_serie") val numeroSerie: String,
    val marca: String,
    val modelo: String,
    val ubicacion: String,
    @SerializedName("fecha_adquisicion") val fechaAdquisicion: String,
    val observaciones: String,
    val activo: Boolean
)

data class AdminEquipoRequestDto(
    val nombre: String,
    @SerializedName("tipo_id") val tipoId: Int? = null,
    @SerializedName("numero_serie") val numeroSerie: String = "",
    val marca: String = "",
    val modelo: String = "",
    val ubicacion: String = "",
    @SerializedName("fecha_adquisicion") val fechaAdquisicion: String = "",
    val observaciones: String = "",
    val activo: Boolean = true
)

data class AdminProgramaItemDto(
    val id: Int,
    @SerializedName("equipo_id") val equipoId: Int,
    @SerializedName("equipo_nombre") val equipoNombre: String,
    val descripcion: String,
    @SerializedName("frecuencia_meses") val frecuenciaMeses: Int,
    @SerializedName("ultima_ejecucion") val ultimaEjecucion: String,
    @SerializedName("proxima_ejecucion") val proximaEjecucion: String,
    val activo: Boolean
)

data class AdminProgramaRequestDto(
    @SerializedName("equipo_id") val equipoId: Int,
    val descripcion: String,
    @SerializedName("frecuencia_meses") val frecuenciaMeses: Int,
    @SerializedName("ultima_ejecucion") val ultimaEjecucion: String,
    val activo: Boolean = true
)

data class AdminPasoItemDto(
    val id: Int,
    val posicion: Int,
    val descripcion: String,
    val observaciones: String,
    @SerializedName("adjunto_nombre") val adjuntoNombre: String,
    val activo: Boolean
)

data class AdminPasoRequestDto(
    val descripcion: String,
    val posicion: Int = 0,
    val observaciones: String = ""
)

data class AdminRepuestoItemDto(
    val id: Int,
    val nombre: String,
    val observaciones: String,
    @SerializedName("stock_actual") val stockActual: Double,
    @SerializedName("stock_minimo") val stockMinimo: Double,
    val activo: Boolean
)

data class AdminRepuestoRequestDto(
    val nombre: String,
    val observaciones: String = "",
    @SerializedName("stock_actual") val stockActual: Double = 0.0,
    @SerializedName("stock_minimo") val stockMinimo: Double = 0.0,
    val activo: Boolean = true
)

data class AdminTecnicoItemDto(
    val id: Int,
    val nombre: String,
    val apellido: String,
    val legajo: String,
    val telefono: String,
    val especialidad: String,
    val activo: Boolean
)

data class AdminTecnicoCreateDto(
    val nombre: String,
    val apellido: String,
    val legajo: String,
    val telefono: String = "",
    val especialidad: String = "",
    val password: String
)

data class AdminTecnicoUpdateDto(
    val nombre: String,
    val apellido: String,
    val legajo: String,
    val telefono: String = "",
    val especialidad: String = "",
    val activo: Boolean = true
)

data class SetPasswordRequestDto(val password: String)

data class AdminOrdenRequestDto(
    @SerializedName("equipo_id") val equipoId: Int,
    val tipo: String,
    val descripcion: String = "",
    @SerializedName("fecha_apertura") val fechaApertura: String,
    @SerializedName("fecha_cierre") val fechaCierre: String = "",
    val estado: String,
    @SerializedName("tecnico_id") val tecnicoId: Int? = null,
    @SerializedName("costo_mano_obra") val costoManoObra: Double = 0.0,
    val observaciones: String = ""
)
