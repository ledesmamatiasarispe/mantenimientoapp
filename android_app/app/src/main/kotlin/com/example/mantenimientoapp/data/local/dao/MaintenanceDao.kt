package com.example.mantenimientoapp.data.local.dao

import androidx.room.*
import com.example.mantenimientoapp.data.local.entity.MaintenanceItem
import kotlinx.coroutines.flow.Flow

@Dao
interface MaintenanceDao {
    @Query("SELECT * FROM maintenance_items")
    fun getAllItems(): Flow<List<MaintenanceItem>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertItem(item: MaintenanceItem)

    @Delete
    suspend fun deleteItem(item: MaintenanceItem)
}
