import '../core/api_client.dart';
import '../models/equipo.dart';
import '../models/repuesto.dart';
import '../models/cronograma.dart';

class BibliotecaService {
  final ApiClient _client;
  BibliotecaService(this._client);

  Future<List<EquipoCard>> listarEquipos() async {
    final data = await _client.get('/api/equipos');
    return (data as List)
        .map((e) => EquipoCard.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<RepuestoDisponible>> listarRepuestos() async {
    final data = await _client.get('/api/repuestos');
    return (data as List)
        .map((e) => RepuestoDisponible.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<CronogramaFila>> cronograma({int? anio}) async {
    final params = <String, dynamic>{};
    if (anio != null) params['anio'] = anio;
    final data =
        await _client.get('/api/cronograma', params: params);
    return (data as List)
        .map((e) => CronogramaFila.fromJson(e as Map<String, dynamic>))
        .toList();
  }
}
