package com.example.mantenimientoapp.domain.repository

import com.example.mantenimientoapp.data.remote.dto.*
import com.example.mantenimientoapp.utils.NetworkResult

interface BibliotecaRepository {
    suspend fun getEquipos(): NetworkResult<List<EquipoCardDto>>
    suspend fun getRepuestos(): NetworkResult<List<RepuestoDisponibleDto>>
    suspend fun getCronograma(anio: Int): NetworkResult<List<CronogramaFilaDto>>
}
