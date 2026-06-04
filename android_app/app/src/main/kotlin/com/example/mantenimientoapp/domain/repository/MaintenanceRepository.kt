package com.example.mantenimientoapp.domain.repository

import com.example.mantenimientoapp.data.local.entity.MaintenanceItem
import kotlinx.coroutines.flow.Flow

interface MaintenanceRepository {
    fun getAllItems(): Flow<List<MaintenanceItem>>
    suspend fun insertItem(item: MaintenanceItem)
    suspend fun deleteItem(item: MaintenanceItem)
}
