import 'package:flutter/material.dart';

class EstadoChip extends StatelessWidget {
  final String estado;
  const EstadoChip(this.estado, {super.key});

  @override
  Widget build(BuildContext context) {
    final (color, label) = switch (estado) {
      'PENDIENTE' => (Colors.orange, 'Pendiente'),
      'EN_PROGRESO' => (Colors.blue, 'En progreso'),
      'COMPLETADA' => (const Color(0xFF0E6B52), 'Completada'),
      'CANCELADA' => (Colors.grey, 'Cancelada'),
      _ => (Colors.grey, estado),
    };
    return Chip(
      label: Text(label,
          style: const TextStyle(
              color: Colors.white, fontSize: 12, fontWeight: FontWeight.w600)),
      backgroundColor: color,
      padding: EdgeInsets.zero,
      materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
      visualDensity: VisualDensity.compact,
    );
  }
}

class TipoChip extends StatelessWidget {
  final String tipo;
  const TipoChip(this.tipo, {super.key});

  @override
  Widget build(BuildContext context) {
    final (color, label) = switch (tipo) {
      'PREVENTIVO' => (const Color(0xFF0E6B52), 'Preventivo'),
      'CORRECTIVO' => (Colors.orange.shade700, 'Correctivo'),
      'MEJORA' => (Colors.blue.shade700, 'Mejora'),
      _ => (Colors.grey, tipo),
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: color.withOpacity(0.15),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: color.withOpacity(0.4)),
      ),
      child: Text(label,
          style: TextStyle(
              color: color, fontSize: 11, fontWeight: FontWeight.w600)),
    );
  }
}
