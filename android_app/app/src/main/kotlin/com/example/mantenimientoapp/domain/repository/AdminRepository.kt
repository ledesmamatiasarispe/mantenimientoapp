package com.example.mantenimientoapp.domain.repository

import com.example.mantenimientoapp.data.remote.dto.*
import com.example.mantenimientoapp.utils.NetworkResult

interface AdminRepository {
    // Tipos equipo
    suspend fun getTiposEquipo(): NetworkResult<List<TipoEquipoItemDto>>
    suspend fun crearTipoEquipo(nombre: String): NetworkResult<TipoEquipoItemDto>
    suspend fun actualizarTipoEquipo(id: Int, nombre: String, activo: Boolean): NetworkResult<TipoEquipoItemDto>
    suspend fun eliminarTipoEquipo(id: Int): NetworkResult<Unit>

    // Equipos
    suspend fun getEquiposAdmin(): NetworkResult<List<AdminEquipoItemDto>>
    suspend fun crearEquipo(req: AdminEquipoRequestDto): NetworkResult<AdminEquipoItemDto>
    suspend fun actualizarEquipo(id: Int, req: AdminEquipoRequestDto): NetworkResult<AdminEquipoItemDto>
    suspend fun eliminarEquipo(id: Int): NetworkResult<Unit>

    // Programas
    suspend fun getProgramasAdmin(): NetworkResult<List<AdminProgramaItemDto>>
    suspend fun crearPrograma(req: AdminProgramaRequestDto): NetworkResult<AdminProgramaItemDto>
    suspend fun actualizarPrograma(id: Int, req: AdminProgramaRequestDto): NetworkResult<AdminProgramaItemDto>
    suspend fun eliminarPrograma(id: Int): NetworkResult<Unit>
    suspend fun getPasos(programaId: Int): NetworkResult<List<AdminPasoItemDto>>
    suspend fun crearPaso(programaId: Int, req: AdminPasoRequestDto): NetworkResult<AdminPasoItemDto>
    suspend fun actualizarPaso(programaId: Int, pasoId: Int, req: AdminPasoRequestDto): NetworkResult<AdminPasoItemDto>
    suspend fun eliminarPaso(programaId: Int, pasoId: Int): NetworkResult<Unit>

    // Repuestos
    suspend fun getRepuestosAdmin(): NetworkResult<List<AdminRepuestoItemDto>>
    suspend fun crearRepuesto(req: AdminRepuestoRequestDto): NetworkResult<AdminRepuestoItemDto>
    suspend fun actualizarRepuesto(id: Int, req: AdminRepuestoRequestDto): NetworkResult<AdminRepuestoItemDto>
    suspend fun eliminarRepuesto(id: Int): NetworkResult<Unit>

    // Técnicos
    suspend fun getTecnicosAdmin(): NetworkResult<List<AdminTecnicoItemDto>>
    suspend fun crearTecnico(req: AdminTecnicoCreateDto): NetworkResult<AdminTecnicoItemDto>
    suspend fun actualizarTecnico(id: Int, req: AdminTecnicoUpdateDto): NetworkResult<AdminTecnicoItemDto>
    suspend fun eliminarTecnico(id: Int): NetworkResult<Unit>
    suspend fun setPassword(id: Int, password: String): NetworkResult<Unit>

    // Órdenes admin
    suspend fun getOrdenesAdmin(): NetworkResult<List<OrdenCardDto>>
    suspend fun actualizarOrden(id: Int, req: AdminOrdenRequestDto): NetworkResult<OrdenCardDto>
    suspend fun eliminarOrden(id: Int): NetworkResult<Unit>
}
