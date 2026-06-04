package com.example.mantenimientoapp.di

import android.content.Context
import androidx.room.Room
import com.example.mantenimientoapp.data.local.MaintenanceDatabase
import com.example.mantenimientoapp.data.local.dao.MaintenanceDao
import com.example.mantenimientoapp.data.repository.MaintenanceRepositoryImpl
import com.example.mantenimientoapp.domain.repository.MaintenanceRepository
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object AppModule {

    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): MaintenanceDatabase {
        return Room.databaseBuilder(
            context,
            MaintenanceDatabase::class.java,
            "maintenance_db"
        ).build()
    }

    @Provides
    fun provideMaintenanceDao(db: MaintenanceDatabase): MaintenanceDao {
        return db.maintenanceDao
    }

    @Provides
    @Singleton
    fun provideMaintenanceRepository(dao: MaintenanceDao): MaintenanceRepository {
        return MaintenanceRepositoryImpl(dao)
    }
}
