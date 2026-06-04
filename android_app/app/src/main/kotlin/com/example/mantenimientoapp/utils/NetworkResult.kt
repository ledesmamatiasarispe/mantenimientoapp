package com.example.mantenimientoapp.utils

import com.google.gson.Gson
import retrofit2.HttpException
import java.io.IOException

sealed class NetworkResult<out T> {
    data class Success<T>(val data: T) : NetworkResult<T>()
    data class Error(val message: String, val code: Int = 0) : NetworkResult<Nothing>()
    data object Loading : NetworkResult<Nothing>()
}

private data class ApiErrorBody(val detail: String?)

suspend fun <T> safeApiCall(call: suspend () -> T): NetworkResult<T> {
    return try {
        NetworkResult.Success(call())
    } catch (e: HttpException) {
        val body = e.response()?.errorBody()?.string()
        val detail = try {
            Gson().fromJson(body, ApiErrorBody::class.java)?.detail
        } catch (_: Exception) { null }
        NetworkResult.Error(detail ?: e.message(), e.code())
    } catch (e: IOException) {
        NetworkResult.Error("Sin conexión al servidor")
    } catch (e: Exception) {
        NetworkResult.Error(e.message ?: "Error desconocido")
    }
}
