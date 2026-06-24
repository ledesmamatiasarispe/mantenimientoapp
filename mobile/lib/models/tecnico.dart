class Tecnico {
  final int id;
  final String nombre;
  final String apellido;
  final String legajo;
  final String telefono;
  final String especialidad;
  final bool esAdmin;
  final bool activo;

  Tecnico({
    required this.id,
    required this.nombre,
    required this.apellido,
    required this.legajo,
    required this.telefono,
    required this.especialidad,
    required this.esAdmin,
    this.activo = true,
  });

  String get nombreCompleto => '$nombre $apellido'.trim();

  factory Tecnico.fromJson(Map<String, dynamic> j) => Tecnico(
        id: j['id'] as int,
        nombre: j['nombre'] as String? ?? '',
        apellido: j['apellido'] as String? ?? '',
        legajo: j['legajo'] as String? ?? '',
        telefono: j['telefono'] as String? ?? '',
        especialidad: j['especialidad'] as String? ?? '',
        esAdmin: j['es_admin'] as bool? ?? false,
        activo: j['activo'] as bool? ?? true,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'nombre': nombre,
        'apellido': apellido,
        'legajo': legajo,
        'telefono': telefono,
        'especialidad': especialidad,
        'es_admin': esAdmin,
        'activo': activo,
      };
}

class AdminTecnicoItem {
  final int id;
  final String nombre;
  final String apellido;
  final String legajo;
  final String telefono;
  final String especialidad;
  final bool activo;

  AdminTecnicoItem({
    required this.id,
    required this.nombre,
    required this.apellido,
    required this.legajo,
    required this.telefono,
    required this.especialidad,
    required this.activo,
  });

  String get nombreCompleto => '$nombre $apellido'.trim();

  factory AdminTecnicoItem.fromJson(Map<String, dynamic> j) => AdminTecnicoItem(
        id: j['id'] as int,
        nombre: j['nombre'] as String? ?? '',
        apellido: j['apellido'] as String? ?? '',
        legajo: j['legajo'] as String? ?? '',
        telefono: j['telefono'] as String? ?? '',
        especialidad: j['especialidad'] as String? ?? '',
        activo: j['activo'] as bool? ?? true,
      );
}
