package com.example.mantenimientoapp.data.repository

import com.example.mantenimientoapp.data.remote.ApiService
import com.example.mantenimientoapp.data.remote.dto.*
import com.example.mantenimientoapp.domain.repository.AdminRepository
import com.example.mantenimientoapp.utils.NetworkResult
import com.example.mantenimientoapp.utils.safeApiCall
import javax.inject.Inject

class AdminRepositoryImpl @Inject constructor(private val api: ApiService) : AdminRepository {

    private suspend fun unitCall(call: suspend () -> retrofit2.Response<Unit>): NetworkResult<Unit> =
        safeApiCall { call().also { check(it.isSuccessful) { it.code().toString() } } }

    override suspend fun getTiposEquipo() = safeApiCall { api.getTiposEquipo() }
    override suspend fun crearTipoEquipo(nombre: String) = safeApiCall { api.crearTipoEquipo(TipoEquipoRequestDto(nombre)) }
    override suspend fun actualizarTipoEquipo(id: Int, nombre: String, activo: Boolean) = safeApiCall { api.actualizarTipoEquipo(id, TipoEquipoRequestDto(nombre, activo)) }
    override suspend fun eliminarTipoEquipo(id: Int) = unitCall { api.eliminarTipoEquipo(id) }

    override suspend fun getEquiposAdmin() = safeApiCall { api.getAdminEquipos() }
    override suspend fun crearEquipo(req: AdminEquipoRequestDto) = safeApiCall { api.crearEquipo(req) }
    override suspend fun actualizarEquipo(id: Int, req: AdminEquipoRequestDto) = safeApiCall { api.actualizarEquipo(id, req) }
    override suspend fun eliminarEquipo(id: Int) = unitCall { api.eliminarEquipo(id) }

    override suspend fun getProgramasAdmin() = safeApiCall { api.getAdminProgramas() }
    override suspend fun crearPrograma(req: AdminProgramaRequestDto) = safeApiCall { api.crearPrograma(req) }
    override suspend fun actualizarPrograma(id: Int, req: AdminProgramaRequestDto) = safeApiCall { api.actualizarPrograma(id, req) }
    override suspend fun eliminarPrograma(id: Int) = unitCall { api.eliminarPrograma(id) }
    override suspend fun getPasos(programaId: Int) = safeApiCall { api.getAdminPasos(programaId) }
    override suspend fun crearPaso(programaId: Int, req: AdminPasoRequestDto) = safeApiCall { api.crearPaso(programaId, req) }
    override suspend fun actualizarPaso(programaId: Int, pasoId: Int, req: AdminPasoRequestDto) = safeApiCall { api.actualizarPaso(programaId, pasoId, req) }
    override suspend fun eliminarPaso(programaId: Int, pasoId: Int) = unitCall { api.eliminarPaso(programaId, pasoId) }

    override suspend fun getRepuestosAdmin() = safeApiCall { api.getAdminRepuestos() }
    override suspend fun crearRepuesto(req: AdminRepuestoRequestDto) = safeApiCall { api.crearRepuesto(req) }
    override suspend fun actualizarRepuesto(id: Int, req: AdminRepuestoRequestDto) = safeApiCall { api.actualizarRepuesto(id, req) }
    override suspend fun eliminarRepuesto(id: Int) = unitCall { api.eliminarRepuesto(id) }

    override suspend fun getTecnicosAdmin() = safeApiCall { api.getAdminTecnicos() }
    override suspend fun crearTecnico(req: AdminTecnicoCreateDto) = safeApiCall { api.crearTecnico(req) }
    override suspend fun actualizarTecnico(id: Int, req: AdminTecnicoUpdateDto) = safeApiCall { api.actualizarTecnico(id, req) }
    override suspend fun eliminarTecnico(id: Int) = unitCall { api.eliminarTecnico(id) }
    override suspend fun setPassword(id: Int, password: String) = unitCall { api.setPasswordTecnico(id, SetPasswordRequestDto(password)) }

    override suspend fun getOrdenesAdmin() = safeApiCall { api.getAdminOrdenes() }
    override suspend fun actualizarOrden(id: Int, req: AdminOrdenRequestDto) = safeApiCall { api.actualizarOrden(id, req) }
    override suspend fun eliminarOrden(id: Int) = unitCall { api.eliminarOrden(id) }
}
