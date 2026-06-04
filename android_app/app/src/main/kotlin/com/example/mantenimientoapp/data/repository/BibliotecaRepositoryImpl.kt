package com.example.mantenimientoapp.data.repository

import com.example.mantenimientoapp.data.remote.ApiService
import com.example.mantenimientoapp.domain.repository.BibliotecaRepository
import com.example.mantenimientoapp.utils.safeApiCall
import javax.inject.Inject

class BibliotecaRepositoryImpl @Inject constructor(
    private val api: ApiService
) : BibliotecaRepository {
    override suspend fun getEquipos() = safeApiCall { api.getEquipos() }
    override suspend fun getRepuestos() = safeApiCall { api.getRepuestos() }
    override suspend fun getCronograma(anio: Int) = safeApiCall { api.getCronograma(anio) }
}
