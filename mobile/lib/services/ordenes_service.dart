import 'dart:io';
import '../core/api_client.dart';
import '../models/orden.dart';

class OrdenesService {
  final ApiClient _client;
  OrdenesService(this._client);

  Future<List<OrdenCard>> listar({
    String? estado,
    int? equipoId,
    bool soloMis = false,
  }) async {
    final params = <String, dynamic>{};
    if (estado != null) params['estado'] = estado;
    if (equipoId != null) params['equipo_id'] = equipoId;
    if (soloMis) params['solo_mis'] = 'true';
    final data =
        await _client.get('/api/ordenes', params: params);
    return (data as List)
        .map((e) => OrdenCard.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<OrdenDetail> obtener(int id) async {
    final data = await _client.get('/api/ordenes/$id');
    return OrdenDetail.fromJson(data as Map<String, dynamic>);
  }

  Future<OrdenDetail> crear({
    required int equipoId,
    required String tipo,
    String descripcion = '',
    String observaciones = '',
  }) async {
    final data = await _client.post('/api/ordenes', body: {
      'equipo_id': equipoId,
      'tipo': tipo,
      'descripcion': descripcion,
      'observaciones': observaciones,
    });
    return OrdenDetail.fromJson(data as Map<String, dynamic>);
  }

  Future<OrdenDetail> aceptar(int id) async {
    final data = await _client.post('/api/ordenes/$id/aceptar');
    return OrdenDetail.fromJson(data as Map<String, dynamic>);
  }

  Future<OrdenDetail> cancelarAceptacion(int id) async {
    final data =
        await _client.post('/api/ordenes/$id/cancelar-aceptacion');
    return OrdenDetail.fromJson(data as Map<String, dynamic>);
  }

  Future<OrdenDetail> completar(int id,
      {String observaciones = '', double? horasTrabajo}) async {
    final body = <String, dynamic>{'observaciones': observaciones};
    if (horasTrabajo != null) {
      body['horas_trabajo'] = horasTrabajo;
    }
    final data =
        await _client.post('/api/ordenes/$id/completar', body: body);
    return OrdenDetail.fromJson(data as Map<String, dynamic>);
  }

  Future<OrdenDetail> agregarRepuesto(
      int ordenId, int repuestoId, double cantidad) async {
    final data =
        await _client.post('/api/ordenes/$ordenId/repuestos', body: {
      'repuesto_id': repuestoId,
      'cantidad': cantidad,
    });
    return OrdenDetail.fromJson(data as Map<String, dynamic>);
  }

  Future<OrdenDetail> quitarRepuesto(int ordenId, int itemId) async {
    final data =
        await _client.delete('/api/ordenes/$ordenId/repuestos/$itemId');
    return OrdenDetail.fromJson(data as Map<String, dynamic>);
  }

  Future<OrdenDetail> agregarObservacion(int id, String texto) async {
    final data = await _client.post('/api/ordenes/$id/observaciones',
        body: {'texto': texto});
    return OrdenDetail.fromJson(data as Map<String, dynamic>);
  }

  Future<OrdenDetail> subirFoto(int id, File foto) async {
    final data =
        await _client.postMultipart('/api/ordenes/$id/fotos', foto, 'foto');
    return OrdenDetail.fromJson(data as Map<String, dynamic>);
  }

  Future<OrdenDetail> eliminarFoto(int ordenId, int fotoId) async {
    final data =
        await _client.delete('/api/ordenes/$ordenId/fotos/$fotoId');
    return OrdenDetail.fromJson(data as Map<String, dynamic>);
  }

  Future<OrdenDetail> togglePaso(int ordenId, int pasoId) async {
    final data =
        await _client.post('/api/ordenes/$ordenId/pasos/$pasoId/toggle');
    return OrdenDetail.fromJson(data as Map<String, dynamic>);
  }

  String fotoUrl(int ordenId, int fotoId) =>
      '${_client.baseUrl}/api/ordenes/$ordenId/fotos/$fotoId';
}
