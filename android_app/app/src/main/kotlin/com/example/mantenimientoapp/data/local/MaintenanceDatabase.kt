package com.example.mantenimientoapp.data.local

import androidx.room.Database
import androidx.room.RoomDatabase
import com.example.mantenimientoapp.data.local.dao.MaintenanceDao
import com.example.mantenimientoapp.data.local.entity.MaintenanceItem

@Database(entities = [MaintenanceItem::class], version = 1, exportSchema = false)
abstract class MaintenanceDatabase : RoomDatabase() {
    abstract val maintenanceDao: MaintenanceDao
}
