package com.example.mantenimientoapp.data.remote

import com.example.mantenimientoapp.data.remote.dto.*
import okhttp3.MultipartBody
import okhttp3.ResponseBody
import retrofit2.Response
import retrofit2.http.*

interface ApiService {

    // ── Health / Network ──────────────────────────────────────────────────────
    @GET("api/health")
    suspend fun health(): retrofit2.Response<Unit>

    @GET("api/network-info")
    suspend fun networkInfo(): NetworkInfoDto

    // ── Auth ──────────────────────────────────────────────────────────────────
    @POST("api/auth/login")
    suspend fun login(@Body request: LoginRequestDto): TokenResponseDto

    @GET("api/auth/me")
    suspend fun me(): TecnicoPublicDto

    // ── Órdenes ───────────────────────────────────────────────────────────────
    @GET("api/ordenes")
    suspend fun getOrdenes(
        @Query("estado") estado: String? = null,
        @Query("solo_mis") soloMis: Boolean? = null
    ): List<OrdenCardDto>

    @GET("api/ordenes/{id}")
    suspend fun getOrden(@Path("id") id: Int): OrdenDetailDto

    @POST("api/ordenes")
    suspend fun crearOrden(@Body request: CrearOrdenRequestDto): OrdenCardDto

    @POST("api/ordenes/{id}/aceptar")
    suspend fun aceptarOrden(@Path("id") id: Int): Response<Unit>

    @POST("api/ordenes/{id}/cancelar-aceptacion")
    suspend fun cancelarAceptacion(@Path("id") id: Int): Response<Unit>

    @POST("api/ordenes/{id}/completar")
    suspend fun completarOrden(
        @Path("id") id: Int,
        @Body request: CompletarOrdenRequestDto
    ): Response<Unit>

    @POST("api/ordenes/{id}/repuestos")
    suspend fun agregarRepuesto(
        @Path("id") id: Int,
        @Body request: AgregarRepuestoRequestDto
    ): Response<Unit>

    @DELETE("api/ordenes/{id}/repuestos/{itemId}")
    suspend fun quitarRepuesto(
        @Path("id") id: Int,
        @Path("itemId") itemId: Int
    ): Response<Unit>

    @POST("api/ordenes/{id}/observaciones")
    suspend fun agregarObservacion(
        @Path("id") id: Int,
        @Body request: ObservacionRequestDto
    ): Response<Unit>

    @POST("api/ordenes/{id}/pasos/{pasoId}/toggle")
    suspend fun togglePaso(
        @Path("id") id: Int,
        @Path("pasoId") pasoId: Int
    ): Response<Unit>

    @Multipart
    @POST("api/ordenes/{id}/fotos")
    suspend fun subirFoto(
        @Path("id") id: Int,
        @Part foto: MultipartBody.Part
    ): Response<Unit>

    @DELETE("api/ordenes/{id}/fotos/{fotoId}")
    suspend fun eliminarFoto(
        @Path("id") id: Int,
        @Path("fotoId") fotoId: Int
    ): Response<Unit>

    @Streaming
    @GET("api/ordenes/{id}/fotos/{fotoId}")
    suspend fun descargarFoto(
        @Path("id") id: Int,
        @Path("fotoId") fotoId: Int
    ): Response<ResponseBody>

    // ── Biblioteca ────────────────────────────────────────────────────────────
    @GET("api/equipos")
    suspend fun getEquipos(): List<EquipoCardDto>

    @GET("api/repuestos")
    suspend fun getRepuestos(): List<RepuestoDisponibleDto>

    @GET("api/cronograma")
    suspend fun getCronograma(@Query("anio") anio: Int): List<CronogramaFilaDto>

    @Streaming
    @GET("api/pasos/{pasoId}/adjunto")
    suspend fun getPasoAdjunto(@Path("pasoId") pasoId: Int): Response<ResponseBody>

    // ── Admin – Tipos Equipo ──────────────────────────────────────────────────
    @GET("api/admin/tipos-equipo")
    suspend fun getTiposEquipo(): List<TipoEquipoItemDto>

    @POST("api/admin/tipos-equipo")
    suspend fun crearTipoEquipo(@Body request: TipoEquipoRequestDto): TipoEquipoItemDto

    @PUT("api/admin/tipos-equipo/{id}")
    suspend fun actualizarTipoEquipo(
        @Path("id") id: Int,
        @Body request: TipoEquipoRequestDto
    ): TipoEquipoItemDto

    @DELETE("api/admin/tipos-equipo/{id}")
    suspend fun eliminarTipoEquipo(@Path("id") id: Int): Response<Unit>

    // ── Admin – Equipos ───────────────────────────────────────────────────────
    @GET("api/admin/equipos")
    suspend fun getAdminEquipos(): List<AdminEquipoItemDto>

    @POST("api/admin/equipos")
    suspend fun crearEquipo(@Body request: AdminEquipoRequestDto): AdminEquipoItemDto

    @PUT("api/admin/equipos/{id}")
    suspend fun actualizarEquipo(
        @Path("id") id: Int,
        @Body request: AdminEquipoRequestDto
    ): AdminEquipoItemDto

    @DELETE("api/admin/equipos/{id}")
    suspend fun eliminarEquipo(@Path("id") id: Int): Response<Unit>

    // ── Admin – Programas ─────────────────────────────────────────────────────
    @GET("api/admin/programas")
    suspend fun getAdminProgramas(): List<AdminProgramaItemDto>

    @POST("api/admin/programas")
    suspend fun crearPrograma(@Body request: AdminProgramaRequestDto): AdminProgramaItemDto

    @PUT("api/admin/programas/{id}")
    suspend fun actualizarPrograma(
        @Path("id") id: Int,
        @Body request: AdminProgramaRequestDto
    ): AdminProgramaItemDto

    @DELETE("api/admin/programas/{id}")
    suspend fun eliminarPrograma(@Path("id") id: Int): Response<Unit>

    @GET("api/admin/programas/{id}/pasos")
    suspend fun getAdminPasos(@Path("id") programaId: Int): List<AdminPasoItemDto>

    @POST("api/admin/programas/{id}/pasos")
    suspend fun crearPaso(
        @Path("id") programaId: Int,
        @Body request: AdminPasoRequestDto
    ): AdminPasoItemDto

    @PUT("api/admin/programas/{id}/pasos/{pasoId}")
    suspend fun actualizarPaso(
        @Path("id") programaId: Int,
        @Path("pasoId") pasoId: Int,
        @Body request: AdminPasoRequestDto
    ): AdminPasoItemDto

    @DELETE("api/admin/programas/{id}/pasos/{pasoId}")
    suspend fun eliminarPaso(
        @Path("id") programaId: Int,
        @Path("pasoId") pasoId: Int
    ): Response<Unit>

    // ── Admin – Repuestos ─────────────────────────────────────────────────────
    @GET("api/admin/repuestos")
    suspend fun getAdminRepuestos(): List<AdminRepuestoItemDto>

    @POST("api/admin/repuestos")
    suspend fun crearRepuesto(@Body request: AdminRepuestoRequestDto): AdminRepuestoItemDto

    @PUT("api/admin/repuestos/{id}")
    suspend fun actualizarRepuesto(
        @Path("id") id: Int,
        @Body request: AdminRepuestoRequestDto
    ): AdminRepuestoItemDto

    @DELETE("api/admin/repuestos/{id}")
    suspend fun eliminarRepuesto(@Path("id") id: Int): Response<Unit>

    // ── Admin – Técnicos ──────────────────────────────────────────────────────
    @GET("api/admin/tecnicos")
    suspend fun getAdminTecnicos(): List<AdminTecnicoItemDto>

    @POST("api/admin/tecnicos")
    suspend fun crearTecnico(@Body request: AdminTecnicoCreateDto): AdminTecnicoItemDto

    @PUT("api/admin/tecnicos/{id}")
    suspend fun actualizarTecnico(
        @Path("id") id: Int,
        @Body request: AdminTecnicoUpdateDto
    ): AdminTecnicoItemDto

    @DELETE("api/admin/tecnicos/{id}")
    suspend fun eliminarTecnico(@Path("id") id: Int): Response<Unit>

    @POST("api/admin/tecnicos/{id}/password")
    suspend fun setPasswordTecnico(
        @Path("id") id: Int,
        @Body request: SetPasswordRequestDto
    ): Response<Unit>

    // ── Admin – Órdenes ───────────────────────────────────────────────────────
    @GET("api/admin/ordenes")
    suspend fun getAdminOrdenes(): List<OrdenCardDto>

    @PUT("api/admin/ordenes/{id}")
    suspend fun actualizarOrden(
        @Path("id") id: Int,
        @Body request: AdminOrdenRequestDto
    ): OrdenCardDto

    @DELETE("api/admin/ordenes/{id}")
    suspend fun eliminarOrden(@Path("id") id: Int): Response<Unit>
}
