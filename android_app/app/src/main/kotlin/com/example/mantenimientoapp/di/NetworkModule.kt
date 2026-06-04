package com.example.mantenimientoapp.di

import com.example.mantenimientoapp.data.preferences.SessionManager
import com.example.mantenimientoapp.data.remote.ApiClient
import com.example.mantenimientoapp.data.remote.ApiService
import com.example.mantenimientoapp.data.repository.*
import com.example.mantenimientoapp.domain.repository.*
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    @Provides @Singleton
    fun provideApiClient(sessionManager: SessionManager): ApiClient =
        ApiClient(sessionManager)

    @Provides @Singleton
    fun provideApiService(client: ApiClient): ApiService = client.service

    @Provides @Singleton
    fun provideAuthRepository(api: ApiService, session: SessionManager): AuthRepository =
        AuthRepositoryImpl(api, session)

    @Provides @Singleton
    fun provideOrdenesRepository(api: ApiService): OrdenesRepository =
        OrdenesRepositoryImpl(api)

    @Provides @Singleton
    fun provideBibliotecaRepository(api: ApiService): BibliotecaRepository =
        BibliotecaRepositoryImpl(api)

    @Provides @Singleton
    fun provideAdminRepository(api: ApiService): AdminRepository =
        AdminRepositoryImpl(api)
}
