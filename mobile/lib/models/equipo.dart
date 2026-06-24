class EquipoCard {
  final int id;
  final String nombre;
  final int? tipoId;
  final String tipoNombre;
  final String numeroSerie;
  final String marca;
  final String modelo;
  final String ubicacion;
  final String observaciones;
  final int programasActivosCount;

  EquipoCard({
    required this.id,
    required this.nombre,
    this.tipoId,
    required this.tipoNombre,
    required this.numeroSerie,
    required this.marca,
    required this.modelo,
    required this.ubicacion,
    required this.observaciones,
    required this.programasActivosCount,
  });

  factory EquipoCard.fromJson(Map<String, dynamic> j) => EquipoCard(
        id: j['id'] as int,
        nombre: j['nombre'] as String? ?? '',
        tipoId: j['tipo_id'] as int?,
        tipoNombre: j['tipo_nombre'] as String? ?? '',
        numeroSerie: j['numero_serie'] as String? ?? '',
        marca: j['marca'] as String? ?? '',
        modelo: j['modelo'] as String? ?? '',
        ubicacion: j['ubicacion'] as String? ?? '',
        observaciones: j['observaciones'] as String? ?? '',
        programasActivosCount:
            j['programas_activos_count'] as int? ?? 0,
      );
}

class AdminEquipoItem {
  final int id;
  final String nombre;
  final int? tipoId;
  final String tipoNombre;
  final String numeroSerie;
  final String marca;
  final String modelo;
  final String ubicacion;
  final String fechaAdquisicion;
  final String observaciones;
  final bool activo;
  final bool horasTrabajoActivo;
  final double horasTrabajoActual;

  AdminEquipoItem({
    required this.id,
    required this.nombre,
    this.tipoId,
    required this.tipoNombre,
    required this.numeroSerie,
    required this.marca,
    required this.modelo,
    required this.ubicacion,
    required this.fechaAdquisicion,
    required this.observaciones,
    required this.activo,
    this.horasTrabajoActivo = false,
    this.horasTrabajoActual = 0.0,
  });

  factory AdminEquipoItem.fromJson(Map<String, dynamic> j) => AdminEquipoItem(
        id: j['id'] as int,
        nombre: j['nombre'] as String? ?? '',
        tipoId: j['tipo_id'] as int?,
        tipoNombre: j['tipo_nombre'] as String? ?? '',
        numeroSerie: j['numero_serie'] as String? ?? '',
        marca: j['marca'] as String? ?? '',
        modelo: j['modelo'] as String? ?? '',
        ubicacion: j['ubicacion'] as String? ?? '',
        fechaAdquisicion: j['fecha_adquisicion'] as String? ?? '',
        observaciones: j['observaciones'] as String? ?? '',
        activo: j['activo'] as bool? ?? true,
        horasTrabajoActivo: j['horas_trabajo_activo'] as bool? ?? false,
        horasTrabajoActual:
            (j['horas_trabajo_actual'] as num? ?? 0).toDouble(),
      );
}

class TipoEquipoItem {
  final int id;
  final String nombre;
  final bool activo;

  TipoEquipoItem(
      {required this.id, required this.nombre, required this.activo});

  factory TipoEquipoItem.fromJson(Map<String, dynamic> j) => TipoEquipoItem(
        id: j['id'] as int,
        nombre: j['nombre'] as String? ?? '',
        activo: j['activo'] as bool? ?? true,
      );
}

class AdminProgramaItem {
  final int id;
  final int equipoId;
  final String equipoNombre;
  final String descripcion;
  final int frecuenciaMeses;
  final String ultimaEjecucion;
  final String proximaEjecucion;
  final bool activo;

  AdminProgramaItem({
    required this.id,
    required this.equipoId,
    required this.equipoNombre,
    required this.descripcion,
    required this.frecuenciaMeses,
    required this.ultimaEjecucion,
    required this.proximaEjecucion,
    required this.activo,
  });

  factory AdminProgramaItem.fromJson(Map<String, dynamic> j) =>
      AdminProgramaItem(
        id: j['id'] as int,
        equipoId: j['equipo_id'] as int,
        equipoNombre: j['equipo_nombre'] as String? ?? '',
        descripcion: j['descripcion'] as String? ?? '',
        frecuenciaMeses: j['frecuencia_meses'] as int? ?? 1,
        ultimaEjecucion: j['ultima_ejecucion'] as String? ?? '',
        proximaEjecucion: j['proxima_ejecucion'] as String? ?? '',
        activo: j['activo'] as bool? ?? true,
      );
}

class AdminPasoItem {
  final int id;
  final int posicion;
  final String descripcion;
  final String observaciones;
  final String adjuntoNombre;
  final bool activo;

  AdminPasoItem({
    required this.id,
    required this.posicion,
    required this.descripcion,
    required this.observaciones,
    required this.adjuntoNombre,
    required this.activo,
  });

  factory AdminPasoItem.fromJson(Map<String, dynamic> j) => AdminPasoItem(
        id: j['id'] as int,
        posicion: j['posicion'] as int? ?? 0,
        descripcion: j['descripcion'] as String? ?? '',
        observaciones: j['observaciones'] as String? ?? '',
        adjuntoNombre: j['adjunto_nombre'] as String? ?? '',
        activo: j['activo'] as bool? ?? true,
      );
}
