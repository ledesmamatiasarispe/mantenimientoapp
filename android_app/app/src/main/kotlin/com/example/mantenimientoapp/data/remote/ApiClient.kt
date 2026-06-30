package com.example.mantenimientoapp.data.remote

import com.example.mantenimientoapp.data.preferences.SessionManager
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import okhttp3.HttpUrl.Companion.toHttpUrl
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

class ApiClient(private val sessionManager: SessionManager) {

    private val okHttpClient = OkHttpClient.Builder()
        .addInterceptor { chain ->
            // Rewrite host/port from DataStore on every request
            val baseUrl = runBlocking { sessionManager.baseUrl.first() }.trimEnd('/') + "/"
            val original = chain.request()
            val newBase = baseUrl.toHttpUrl()
            val newUrl = original.url.newBuilder()
                .scheme(newBase.scheme)
                .host(newBase.host)
                .port(newBase.port)
                .build()
            chain.proceed(original.newBuilder().url(newUrl).build())
        }
        .addInterceptor { chain ->
            // Inject JWT token
            val token = runBlocking { sessionManager.token.first() }
            val req = if (token != null) {
                chain.request().newBuilder()
                    .addHeader("Authorization", "Bearer $token")
                    .build()
            } else chain.request()
            chain.proceed(req)
        }
        .addInterceptor(
            HttpLoggingInterceptor().apply {
                level = HttpLoggingInterceptor.Level.BASIC
            }
        )
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .build()

    val service: ApiService = Retrofit.Builder()
        .baseUrl("http://localhost:50502/")
        .client(okHttpClient)
        .addConverterFactory(GsonConverterFactory.create())
        .build()
        .create(ApiService::class.java)
}
