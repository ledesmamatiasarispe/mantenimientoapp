package com.example.mantenimientoapp.data.repository

import com.example.mantenimientoapp.data.remote.ApiService
import com.example.mantenimientoapp.data.remote.dto.*
import com.example.mantenimientoapp.domain.repository.OrdenesRepository
import com.example.mantenimientoapp.utils.NetworkResult
import com.example.mantenimientoapp.utils.safeApiCall
import javax.inject.Inject

class OrdenesRepositoryImpl @Inject constructor(
    private val api: ApiService
) : OrdenesRepository {

    override suspend fun getOrdenes(estado: String?, soloMis: Boolean) =
        safeApiCall { api.getOrdenes(estado, if (soloMis) true else null) }

    override suspend fun getOrden(id: Int) =
        safeApiCall { api.getOrden(id) }

    override suspend fun crearOrden(equipoId: Int, tipo: String, descripcion: String, observaciones: String) =
        safeApiCall { api.crearOrden(CrearOrdenRequestDto(equipoId, tipo, descripcion, observaciones)) }

    override suspend fun aceptarOrden(id: Int): NetworkResult<Unit> =
        safeApiCall { api.aceptarOrden(id).also { check(it.isSuccessful) { it.code().toString() } } }

    override suspend fun cancelarAceptacion(id: Int): NetworkResult<Unit> =
        safeApiCall { api.cancelarAceptacion(id).also { check(it.isSuccessful) { it.code().toString() } } }

    override suspend fun completarOrden(id: Int, observaciones: String): NetworkResult<Unit> =
        safeApiCall { api.completarOrden(id, CompletarOrdenRequestDto(observaciones)).also { check(it.isSuccessful) { it.code().toString() } } }

    override suspend fun agregarRepuesto(ordenId: Int, repuestoId: Int, cantidad: Double): NetworkResult<Unit> =
        safeApiCall { api.agregarRepuesto(ordenId, AgregarRepuestoRequestDto(repuestoId, cantidad)).also { check(it.isSuccessful) { it.code().toString() } } }

    override suspend fun quitarRepuesto(ordenId: Int, itemId: Int): NetworkResult<Unit> =
        safeApiCall { api.quitarRepuesto(ordenId, itemId).also { check(it.isSuccessful) { it.code().toString() } } }

    override suspend fun agregarObservacion(ordenId: Int, texto: String): NetworkResult<Unit> =
        safeApiCall { api.agregarObservacion(ordenId, ObservacionRequestDto(texto)).also { check(it.isSuccessful) { it.code().toString() } } }

    override suspend fun togglePaso(ordenId: Int, pasoId: Int): NetworkResult<Unit> =
        safeApiCall { api.togglePaso(ordenId, pasoId).also { check(it.isSuccessful) { it.code().toString() } } }

    override suspend fun eliminarFoto(ordenId: Int, fotoId: Int): NetworkResult<Unit> =
        safeApiCall { api.eliminarFoto(ordenId, fotoId).also { check(it.isSuccessful) { it.code().toString() } } }

    override fun getFotoUrl(baseUrl: String, ordenId: Int, fotoId: Int, token: String): String =
        "${baseUrl.trimEnd('/')}/api/ordenes/$ordenId/fotos/$fotoId"
}
