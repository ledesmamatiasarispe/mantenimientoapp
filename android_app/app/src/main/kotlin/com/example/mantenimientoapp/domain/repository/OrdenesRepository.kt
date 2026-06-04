package com.example.mantenimientoapp.domain.repository

import com.example.mantenimientoapp.data.remote.dto.*
import com.example.mantenimientoapp.utils.NetworkResult

interface OrdenesRepository {
    suspend fun getOrdenes(estado: String? = null, soloMis: Boolean = false): NetworkResult<List<OrdenCardDto>>
    suspend fun getOrden(id: Int): NetworkResult<OrdenDetailDto>
    suspend fun crearOrden(equipoId: Int, tipo: String, descripcion: String, observaciones: String): NetworkResult<OrdenCardDto>
    suspend fun aceptarOrden(id: Int): NetworkResult<Unit>
    suspend fun cancelarAceptacion(id: Int): NetworkResult<Unit>
    suspend fun completarOrden(id: Int, observaciones: String): NetworkResult<Unit>
    suspend fun agregarRepuesto(ordenId: Int, repuestoId: Int, cantidad: Double): NetworkResult<Unit>
    suspend fun quitarRepuesto(ordenId: Int, itemId: Int): NetworkResult<Unit>
    suspend fun agregarObservacion(ordenId: Int, texto: String): NetworkResult<Unit>
    suspend fun togglePaso(ordenId: Int, pasoId: Int): NetworkResult<Unit>
    suspend fun eliminarFoto(ordenId: Int, fotoId: Int): NetworkResult<Unit>
    fun getFotoUrl(baseUrl: String, ordenId: Int, fotoId: Int, token: String): String
}
