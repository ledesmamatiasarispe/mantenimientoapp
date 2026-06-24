class RepuestoDisponible {
  final int id;
  final String nombre;
  final double stockActual;
  final double stockMinimo;

  RepuestoDisponible({
    required this.id,
    required this.nombre,
    required this.stockActual,
    required this.stockMinimo,
  });

  bool get stockBajo => stockActual <= stockMinimo;

  factory RepuestoDisponible.fromJson(Map<String, dynamic> j) =>
      RepuestoDisponible(
        id: j['id'] as int,
        nombre: j['nombre'] as String? ?? '',
        stockActual: (j['stock_actual'] as num? ?? 0).toDouble(),
        stockMinimo: (j['stock_minimo'] as num? ?? 0).toDouble(),
      );
}

class AdminRepuestoItem {
  final int id;
  final String nombre;
  final String observaciones;
  final double stockActual;
  final double stockMinimo;
  final bool activo;

  AdminRepuestoItem({
    required this.id,
    required this.nombre,
    required this.observaciones,
    required this.stockActual,
    required this.stockMinimo,
    required this.activo,
  });

  bool get stockBajo => stockActual <= stockMinimo;

  factory AdminRepuestoItem.fromJson(Map<String, dynamic> j) =>
      AdminRepuestoItem(
        id: j['id'] as int,
        nombre: j['nombre'] as String? ?? '',
        observaciones: j['observaciones'] as String? ?? '',
        stockActual: (j['stock_actual'] as num? ?? 0).toDouble(),
        stockMinimo: (j['stock_minimo'] as num? ?? 0).toDouble(),
        activo: j['activo'] as bool? ?? true,
      );
}
