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

// ── Alertas ───────────────────────────────────────────────────────────────────

data class AlertaItemDto(
    val key: String,
    val tipo: String,
    val mensaje: String,
    val severidad: String,
    @SerializedName("puede_posponer") val puedePosponer: Boolean = true
)

data class SnoozeRequestDto(val dias: Int = 7)

// ── Dashboard ─────────────────────────────────────────────────────────────────

data class DashboardStatsDto(
    @SerializedName("ordenes_pendientes") val ordenesPendientes: Int,
    @SerializedName("ordenes_en_progreso") val ordenesEnProgreso: Int,
    @SerializedName("ordenes_completadas_mes") val ordenesCompletadasMes: Int,
    @SerializedName("equipos_activos") val equiposActivos: Int,
    @SerializedName("alertas_activas") val alertasActivas: Int,
    @SerializedName("repuestos_bajo_stock") val repuestosBajoStock: Int,
    @SerializedName("programas_vencidos") val programasVencidos: Int
)

// ── Horas de trabajo ──────────────────────────────────────────────────────────

data class HorasOrdenRequestDto(@SerializedName("horas_trabajo") val horasTrabajo: Double)

data class HorasEquipoRequestDto(
    @SerializedName("horas_trabajo_activo") val horasTrabajoActivo: Boolean? = null,
    @SerializedName("horas_trabajo_actual") val horasTrabajoActual: Double? = null
)

// ── Generar órdenes ───────────────────────────────────────────────────────────

data class GenerarOrdenesRequestDto(val mes: Int, val anio: Int)

data class GenerarOrdenesResultDto(
    val creadas: Int,
    val existentes: Int,
    val ordenes: List<Int>
)

// ── Historial de equipo ───────────────────────────────────────────────────────

data class HistorialEquipoItemDto(
    val id: Int,
    val tipo: String,
    val descripcion: String,
    val estado: String,
    @SerializedName("fecha_apertura") val fechaApertura: String,
    @SerializedName("fecha_cierre") val fechaCierre: String,
    @SerializedName("tecnico_nombre") val tecnicoNombre: String,
    @SerializedName("horas_trabajo") val horasTrabajo: Double,
    @SerializedName("costo_mano_obra") val costoManoObra: Double,
    val observaciones: String
)

// ── Electricidad ──────────────────────────────────────────────────────────────

data class MedidorItemDto(
    val id: Int,
    val nombre: String,
    @SerializedName("nro_medidor") val nroMedidor: String,
    @SerializedName("nro_cliente") val nroCliente: String,
    val descripcion: String,
    val activo: Boolean
)

data class MedidorRequestDto(
    val nombre: String,
    @SerializedName("nro_medidor") val nroMedidor: String = "",
    @SerializedName("nro_cliente") val nroCliente: String = "",
    val descripcion: String = "",
    val activo: Boolean = true
)

data class FacturaElectricaItemDto(
    val id: Int,
    @SerializedName("medidor_id") val medidorId: Int,
    val periodo: String,
    @SerializedName("tipo_tarifa") val tipoTarifa: String,
    @SerializedName("fecha_factura") val fechaFactura: String,
    @SerializedName("kwh_punta") val kwhPunta: Double,
    @SerializedName("kwh_valle_noc") val kwhValleNoc: Double,
    @SerializedName("kwh_restantes") val kwhRestantes: Double,
    @SerializedName("kvar_reactiva") val kvarReactiva: Double,
    @SerializedName("drp_kw") val drpKw: Double,
    @SerializedName("drfp_kw") val drfpKw: Double,
    val importe: Double,
    val observaciones: String
)

data class GraficoPuntoDto(val periodo: String, val valor: Double)

data class FacturaElectricaRequestDto(
    val periodo: String,
    @SerializedName("tipo_tarifa") val tipoTarifa: String = "T2",
    @SerializedName("fecha_factura") val fechaFactura: String = "",
    @SerializedName("kwh_punta") val kwhPunta: Double = 0.0,
    @SerializedName("kwh_valle_noc") val kwhValleNoc: Double = 0.0,
    @SerializedName("kwh_restantes") val kwhRestantes: Double = 0.0,
    @SerializedName("kvar_reactiva") val kvarReactiva: Double = 0.0,
    @SerializedName("drp_kw") val drpKw: Double = 0.0,
    @SerializedName("drfp_kw") val drfpKw: Double = 0.0,
    val importe: Double = 0.0,
    val observaciones: String = ""
)

data class GraficoElectricidadDto(
    @SerializedName("consumo_kwh") val consumoKwh: List<GraficoPuntoDto>,
    @SerializedName("demanda_kw") val demandaKw: List<GraficoPuntoDto>,
    @SerializedName("factor_potencia") val factorPotencia: List<GraficoPuntoDto>,
    @SerializedName("energia_reactiva") val energiaReactiva: List<GraficoPuntoDto>,
    @SerializedName("costo_total") val costoTotal: List<GraficoPuntoDto>
)
