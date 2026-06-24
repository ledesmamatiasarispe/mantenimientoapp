class CronogramaFila {
  final int programaId;
  final int equipoId;
  final String equipoNombre;
  final String etiqueta;
  final Map<String, String> meses; // "1".."12" -> "planned"|"activa"|"completada"

  CronogramaFila({
    required this.programaId,
    required this.equipoId,
    required this.equipoNombre,
    required this.etiqueta,
    required this.meses,
  });

  factory CronogramaFila.fromJson(Map<String, dynamic> j) => CronogramaFila(
        programaId: j['programa_id'] as int,
        equipoId: j['equipo_id'] as int,
        equipoNombre: j['equipo_nombre'] as String? ?? '',
        etiqueta: j['etiqueta'] as String? ?? '',
        meses: Map<String, String>.from(
            (j['meses'] as Map<String, dynamic>? ?? {})
                .map((k, v) => MapEntry(k, v.toString()))),
      );
}
