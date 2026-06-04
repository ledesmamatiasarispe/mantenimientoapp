package com.example.mantenimientoapp.data.remote.dto

import com.google.gson.annotations.SerializedName

data class OrdenCardDto(
    val id: Int,
    @SerializedName("equipo_id") val equipoId: Int,
    @SerializedName("equipo_nombre") val equipoNombre: String,
    @SerializedName("equipo_tipo_nombre") val equipoTipoNombre: String,
    @SerializedName("equipo_marca") val equipoMarca: String,
    @SerializedName("equipo_modelo") val equipoModelo: String,
    @SerializedName("equipo_ubicacion") val equipoUbicacion: String,
    val tipo: String,
    val descripcion: String,
    @SerializedName("fecha_apertura") val fechaApertura: String,
    @SerializedName("fecha_cierre") val fechaCierre: String,
    val estado: String,
    @SerializedName("tecnico_id") val tecnicoId: Int?,
    @SerializedName("tecnico_nombre") val tecnicoNombre: String,
    @SerializedName("costo_mano_obra") val costoManoObra: Double,
    val observaciones: String
)

data class ColaboradorItemDto(
    val id: Int,
    val nombre: String,
    val apellido: String
)

data class FotoOrdenItemDto(
    val id: Int,
    val nombre: String
)

data class RepuestoOrdenItemDto(
    val id: Int,
    @SerializedName("repuesto_id") val repuestoId: Int?,
    val descripcion: String,
    val cantidad: Double,
    @SerializedName("costo_unitario") val costoUnitario: Double
)

data class PasoItemDto(
    val id: Int,
    val posicion: Int,
    val descripcion: String,
    val completado: Boolean = false,
    @SerializedName("adjunto_nombre") val adjuntoNombre: String = "",
    val observaciones: String = ""
)

data class ProgramaAdjuntoItemDto(
    val id: Int,
    val tipo: String,
    val nombre: String
)

data class ProgramaResumenDto(
    val id: Int,
    val descripcion: String,
    @SerializedName("frecuencia_meses") val frecuenciaMeses: Int,
    @SerializedName("ultima_ejecucion") val ultimaEjecucion: String,
    @SerializedName("proxima_ejecucion") val proximaEjecucion: String,
    val adjuntos: List<ProgramaAdjuntoItemDto>,
    val pasos: List<PasoItemDto> = emptyList()
)

data class OrdenDetailDto(
    val id: Int,
    @SerializedName("equipo_id") val equipoId: Int,
    @SerializedName("equipo_nombre") val equipoNombre: String,
    @SerializedName("equipo_tipo_nombre") val equipoTipoNombre: String,
    @SerializedName("equipo_marca") val equipoMarca: String,
    @SerializedName("equipo_modelo") val equipoModelo: String,
    @SerializedName("equipo_ubicacion") val equipoUbicacion: String,
    val tipo: String,
    val descripcion: String,
    @SerializedName("fecha_apertura") val fechaApertura: String,
    @SerializedName("fecha_cierre") val fechaCierre: String,
    val estado: String,
    @SerializedName("tecnico_id") val tecnicoId: Int?,
    @SerializedName("tecnico_nombre") val tecnicoNombre: String,
    @SerializedName("costo_mano_obra") val costoManoObra: Double,
    val observaciones: String,
    val repuestos: List<RepuestoOrdenItemDto>,
    val programas: List<ProgramaResumenDto>,
    val colaboradores: List<ColaboradorItemDto>,
    val fotos: List<FotoOrdenItemDto>
)

data class CrearOrdenRequestDto(
    @SerializedName("equipo_id") val equipoId: Int,
    val tipo: String = "CORRECTIVO",
    val descripcion: String = "",
    val observaciones: String = ""
)

data class AgregarRepuestoRequestDto(
    @SerializedName("repuesto_id") val repuestoId: Int,
    val cantidad: Double = 1.0
)

data class ObservacionRequestDto(val texto: String)

data class CompletarOrdenRequestDto(val observaciones: String = "")
