import '../core/api_client.dart';
import '../models/equipo.dart';
import '../models/repuesto.dart';
import '../models/tecnico.dart';
import '../models/orden.dart';

class AdminService {
  final ApiClient _client;
  AdminService(this._client);

  // ── Tipos de Equipo ───────────────────────────────────────────────────────

  Future<List<TipoEquipoItem>> listarTipos() async {
    final data = await _client.get('/api/admin/tipos-equipo');
    return (data as List)
        .map((e) => TipoEquipoItem.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<TipoEquipoItem> crearTipo(String nombre) async {
    final data = await _client.post('/api/admin/tipos-equipo',
        body: {'nombre': nombre, 'activo': true});
    return TipoEquipoItem.fromJson(data as Map<String, dynamic>);
  }

  Future<TipoEquipoItem> actualizarTipo(
      int id, String nombre, bool activo) async {
    final data = await _client.put('/api/admin/tipos-equipo/$id',
        body: {'nombre': nombre, 'activo': activo});
    return TipoEquipoItem.fromJson(data as Map<String, dynamic>);
  }

  Future<void> eliminarTipo(int id) async {
    await _client.delete('/api/admin/tipos-equipo/$id');
  }

  // ── Equipos ───────────────────────────────────────────────────────────────

  Future<List<AdminEquipoItem>> listarEquipos() async {
    final data = await _client.get('/api/admin/equipos');
    return (data as List)
        .map((e) => AdminEquipoItem.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<AdminEquipoItem> crearEquipo(Map<String, dynamic> body) async {
    final data = await _client.post('/api/admin/equipos', body: body);
    return AdminEquipoItem.fromJson(data as Map<String, dynamic>);
  }

  Future<AdminEquipoItem> actualizarEquipo(
      int id, Map<String, dynamic> body) async {
    final data = await _client.put('/api/admin/equipos/$id', body: body);
    return AdminEquipoItem.fromJson(data as Map<String, dynamic>);
  }

  Future<void> eliminarEquipo(int id) async {
    await _client.delete('/api/admin/equipos/$id');
  }

  // ── Repuestos ─────────────────────────────────────────────────────────────

  Future<List<AdminRepuestoItem>> listarRepuestos() async {
    final data = await _client.get('/api/admin/repuestos');
    return (data as List)
        .map((e) => AdminRepuestoItem.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<AdminRepuestoItem> crearRepuesto(Map<String, dynamic> body) async {
    final data = await _client.post('/api/admin/repuestos', body: body);
    return AdminRepuestoItem.fromJson(data as Map<String, dynamic>);
  }

  Future<AdminRepuestoItem> actualizarRepuesto(
      int id, Map<String, dynamic> body) async {
    final data = await _client.put('/api/admin/repuestos/$id', body: body);
    return AdminRepuestoItem.fromJson(data as Map<String, dynamic>);
  }

  Future<void> eliminarRepuesto(int id) async {
    await _client.delete('/api/admin/repuestos/$id');
  }

  // ── Técnicos ──────────────────────────────────────────────────────────────

  Future<List<AdminTecnicoItem>> listarTecnicos() async {
    final data = await _client.get('/api/admin/tecnicos');
    return (data as List)
        .map((e) => AdminTecnicoItem.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<AdminTecnicoItem> crearTecnico(Map<String, dynamic> body) async {
    final data = await _client.post('/api/admin/tecnicos', body: body);
    return AdminTecnicoItem.fromJson(data as Map<String, dynamic>);
  }

  Future<AdminTecnicoItem> actualizarTecnico(
      int id, Map<String, dynamic> body) async {
    final data = await _client.put('/api/admin/tecnicos/$id', body: body);
    return AdminTecnicoItem.fromJson(data as Map<String, dynamic>);
  }

  Future<void> eliminarTecnico(int id) async {
    await _client.delete('/api/admin/tecnicos/$id');
  }

  Future<void> cambiarPassword(int id, String password) async {
    await _client.post('/api/admin/tecnicos/$id/password',
        body: {'password': password});
  }

  // ── Programas ─────────────────────────────────────────────────────────────

  Future<List<AdminProgramaItem>> listarProgramas() async {
    final data = await _client.get('/api/admin/programas');
    return (data as List)
        .map((e) => AdminProgramaItem.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<AdminProgramaItem> crearPrograma(Map<String, dynamic> body) async {
    final data = await _client.post('/api/admin/programas', body: body);
    return AdminProgramaItem.fromJson(data as Map<String, dynamic>);
  }

  Future<AdminProgramaItem> actualizarPrograma(
      int id, Map<String, dynamic> body) async {
    final data = await _client.put('/api/admin/programas/$id', body: body);
    return AdminProgramaItem.fromJson(data as Map<String, dynamic>);
  }

  Future<void> eliminarPrograma(int id) async {
    await _client.delete('/api/admin/programas/$id');
  }

  Future<List<AdminPasoItem>> listarPasos(int programaId) async {
    final data =
        await _client.get('/api/admin/programas/$programaId/pasos');
    return (data as List)
        .map((e) => AdminPasoItem.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<AdminPasoItem> crearPaso(
      int programaId, String descripcion, String observaciones) async {
    final data = await _client.post(
        '/api/admin/programas/$programaId/pasos',
        body: {'descripcion': descripcion, 'observaciones': observaciones});
    return AdminPasoItem.fromJson(data as Map<String, dynamic>);
  }

  Future<AdminPasoItem> actualizarPaso(
      int programaId, int pasoId, Map<String, dynamic> body) async {
    final data = await _client.put(
        '/api/admin/programas/$programaId/pasos/$pasoId',
        body: body);
    return AdminPasoItem.fromJson(data as Map<String, dynamic>);
  }

  Future<void> eliminarPaso(int programaId, int pasoId) async {
    await _client
        .delete('/api/admin/programas/$programaId/pasos/$pasoId');
  }

  // ── Órdenes admin ─────────────────────────────────────────────────────────

  Future<List<OrdenCard>> listarOrdenesAdmin() async {
    final data = await _client.get('/api/admin/ordenes');
    return (data as List)
        .map((e) => OrdenCard.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<void> eliminarOrden(int id) async {
    await _client.delete('/api/admin/ordenes/$id');
  }
}
