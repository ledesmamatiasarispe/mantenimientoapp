package com.example.mantenimientoapp.data.repository

import com.example.mantenimientoapp.data.local.dao.MaintenanceDao
import com.example.mantenimientoapp.data.local.entity.MaintenanceItem
import com.example.mantenimientoapp.domain.repository.MaintenanceRepository
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject

class MaintenanceRepositoryImpl @Inject constructor(
    private val dao: MaintenanceDao
) : MaintenanceRepository {
    override fun getAllItems(): Flow<List<MaintenanceItem>> = dao.getAllItems()

    override suspend fun insertItem(item: MaintenanceItem) = dao.insertItem(item)

    override suspend fun deleteItem(item: MaintenanceItem) = dao.deleteItem(item)
}
