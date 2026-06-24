class RepuestoOrdenItem {
  final int id;
  final int? repuestoId;
  final String descripcion;
  final double cantidad;
  final double costoUnitario;

  RepuestoOrdenItem({
    required this.id,
    this.repuestoId,
    required this.descripcion,
    required this.cantidad,
    required this.costoUnitario,
  });

  factory RepuestoOrdenItem.fromJson(Map<String, dynamic> j) => RepuestoOrdenItem(
        id: j['id'] as int,
        repuestoId: j['repuesto_id'] as int?,
        descripcion: j['descripcion'] as String? ?? '',
        cantidad: (j['cantidad'] as num? ?? 0).toDouble(),
        costoUnitario: (j['costo_unitario'] as num? ?? 0).toDouble(),
      );
}

class PasoItem {
  final int id;
  final int posicion;
  final String descripcion;
  final bool completado;
  final String adjuntoNombre;
  final String observaciones;

  PasoItem({
    required this.id,
    required this.posicion,
    required this.descripcion,
    required this.completado,
    required this.adjuntoNombre,
    required this.observaciones,
  });

  factory PasoItem.fromJson(Map<String, dynamic> j) => PasoItem(
        id: j['id'] as int,
        posicion: j['posicion'] as int? ?? 0,
        descripcion: j['descripcion'] as String? ?? '',
        completado: j['completado'] as bool? ?? false,
        adjuntoNombre: j['adjunto_nombre'] as String? ?? '',
        observaciones: j['observaciones'] as String? ?? '',
      );
}

class ProgramaAdjuntoItem {
  final int id;
  final String tipo;
  final String nombre;

  ProgramaAdjuntoItem(
      {required this.id, required this.tipo, required this.nombre});

  factory ProgramaAdjuntoItem.fromJson(Map<String, dynamic> j) =>
      ProgramaAdjuntoItem(
        id: j['id'] as int,
        tipo: j['tipo'] as String? ?? '',
        nombre: j['nombre'] as String? ?? '',
      );
}

class ProgramaResumen {
  final int id;
  final String descripcion;
  final int frecuenciaMeses;
  final String ultimaEjecucion;
  final String proximaEjecucion;
  final List<ProgramaAdjuntoItem> adjuntos;
  final List<PasoItem> pasos;

  ProgramaResumen({
    required this.id,
    required this.descripcion,
    required this.frecuenciaMeses,
    required this.ultimaEjecucion,
    required this.proximaEjecucion,
    required this.adjuntos,
    required this.pasos,
  });

  factory ProgramaResumen.fromJson(Map<String, dynamic> j) => ProgramaResumen(
        id: j['id'] as int,
        descripcion: j['descripcion'] as String? ?? '',
        frecuenciaMeses: j['frecuencia_meses'] as int? ?? 0,
        ultimaEjecucion: j['ultima_ejecucion'] as String? ?? '',
        proximaEjecucion: j['proxima_ejecucion'] as String? ?? '',
        adjuntos: (j['adjuntos'] as List<dynamic>? ?? [])
            .map((e) =>
                ProgramaAdjuntoItem.fromJson(e as Map<String, dynamic>))
            .toList(),
        pasos: (j['pasos'] as List<dynamic>? ?? [])
            .map((e) => PasoItem.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

class FotoOrdenItem {
  final int id;
  final String nombre;

  FotoOrdenItem({required this.id, required this.nombre});

  factory FotoOrdenItem.fromJson(Map<String, dynamic> j) => FotoOrdenItem(
        id: j['id'] as int,
        nombre: j['nombre'] as String? ?? '',
      );
}

class ColaboradorItem {
  final int id;
  final String nombre;
  final String apellido;

  ColaboradorItem(
      {required this.id, required this.nombre, required this.apellido});

  String get nombreCompleto => '$nombre $apellido'.trim();

  factory ColaboradorItem.fromJson(Map<String, dynamic> j) => ColaboradorItem(
        id: j['id'] as int,
        nombre: j['nombre'] as String? ?? '',
        apellido: j['apellido'] as String? ?? '',
      );
}

class OrdenCard {
  final int id;
  final int equipoId;
  final String equipoNombre;
  final String equipoTipoNombre;
  final String equipoMarca;
  final String equipoModelo;
  final String equipoUbicacion;
  final bool equipoHorasTrabajoActivo;
  final double equipoHorasTrabajoActual;
  final String tipo;
  final String descripcion;
  final String fechaApertura;
  final String fechaCierre;
  final String estado;
  final int? tecnicoId;
  final String tecnicoNombre;
  final double costoManoObra;
  final String observaciones;
  final double? horasTrabajo;

  OrdenCard({
    required this.id,
    required this.equipoId,
    required this.equipoNombre,
    required this.equipoTipoNombre,
    required this.equipoMarca,
    required this.equipoModelo,
    required this.equipoUbicacion,
    this.equipoHorasTrabajoActivo = false,
    this.equipoHorasTrabajoActual = 0.0,
    required this.tipo,
    required this.descripcion,
    required this.fechaApertura,
    required this.fechaCierre,
    required this.estado,
    this.tecnicoId,
    required this.tecnicoNombre,
    required this.costoManoObra,
    required this.observaciones,
    this.horasTrabajo,
  });

  factory OrdenCard.fromJson(Map<String, dynamic> j) => OrdenCard(
        id: j['id'] as int,
        equipoId: j['equipo_id'] as int,
        equipoNombre: j['equipo_nombre'] as String? ?? '',
        equipoTipoNombre: j['equipo_tipo_nombre'] as String? ?? '',
        equipoMarca: j['equipo_marca'] as String? ?? '',
        equipoModelo: j['equipo_modelo'] as String? ?? '',
        equipoUbicacion: j['equipo_ubicacion'] as String? ?? '',
        equipoHorasTrabajoActivo:
            j['equipo_horas_trabajo_activo'] as bool? ?? false,
        equipoHorasTrabajoActual:
            (j['equipo_horas_trabajo_actual'] as num? ?? 0).toDouble(),
        tipo: j['tipo'] as String? ?? '',
        descripcion: j['descripcion'] as String? ?? '',
        fechaApertura: j['fecha_apertura'] as String? ?? '',
        fechaCierre: j['fecha_cierre'] as String? ?? '',
        estado: j['estado'] as String? ?? '',
        tecnicoId: j['tecnico_id'] as int?,
        tecnicoNombre: j['tecnico_nombre'] as String? ?? '',
        costoManoObra: (j['costo_mano_obra'] as num? ?? 0).toDouble(),
        observaciones: j['observaciones'] as String? ?? '',
        horasTrabajo: (j['horas_trabajo'] as num?)?.toDouble(),
      );
}

class OrdenDetail extends OrdenCard {
  final List<RepuestoOrdenItem> repuestos;
  final List<ProgramaResumen> programas;
  final List<ColaboradorItem> colaboradores;
  final List<FotoOrdenItem> fotos;

  OrdenDetail({
    required super.id,
    required super.equipoId,
    required super.equipoNombre,
    required super.equipoTipoNombre,
    required super.equipoMarca,
    required super.equipoModelo,
    required super.equipoUbicacion,
    super.equipoHorasTrabajoActivo,
    super.equipoHorasTrabajoActual,
    required super.tipo,
    required super.descripcion,
    required super.fechaApertura,
    required super.fechaCierre,
    required super.estado,
    super.tecnicoId,
    required super.tecnicoNombre,
    required super.costoManoObra,
    required super.observaciones,
    super.horasTrabajo,
    required this.repuestos,
    required this.programas,
    required this.colaboradores,
    required this.fotos,
  });

  factory OrdenDetail.fromJson(Map<String, dynamic> j) {
    final base = OrdenCard.fromJson(j);
    return OrdenDetail(
      id: base.id,
      equipoId: base.equipoId,
      equipoNombre: base.equipoNombre,
      equipoTipoNombre: base.equipoTipoNombre,
      equipoMarca: base.equipoMarca,
      equipoModelo: base.equipoModelo,
      equipoUbicacion: base.equipoUbicacion,
      equipoHorasTrabajoActivo: base.equipoHorasTrabajoActivo,
      equipoHorasTrabajoActual: base.equipoHorasTrabajoActual,
      tipo: base.tipo,
      descripcion: base.descripcion,
      fechaApertura: base.fechaApertura,
      fechaCierre: base.fechaCierre,
      estado: base.estado,
      tecnicoId: base.tecnicoId,
      tecnicoNombre: base.tecnicoNombre,
      costoManoObra: base.costoManoObra,
      observaciones: base.observaciones,
      horasTrabajo: base.horasTrabajo,
      repuestos: (j['repuestos'] as List<dynamic>? ?? [])
          .map((e) =>
              RepuestoOrdenItem.fromJson(e as Map<String, dynamic>))
          .toList(),
      programas: (j['programas'] as List<dynamic>? ?? [])
          .map((e) => ProgramaResumen.fromJson(e as Map<String, dynamic>))
          .toList(),
      colaboradores: (j['colaboradores'] as List<dynamic>? ?? [])
          .map((e) =>
              ColaboradorItem.fromJson(e as Map<String, dynamic>))
          .toList(),
      fotos: (j['fotos'] as List<dynamic>? ?? [])
          .map((e) => FotoOrdenItem.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}
