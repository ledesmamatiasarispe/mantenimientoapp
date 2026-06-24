import 'package:flutter/material.dart';
import '../../core/api_client.dart';
import '../../models/cronograma.dart';
import '../../services/biblioteca_service.dart';
import '../../widgets/app_error.dart';

class CronogramaScreen extends StatefulWidget {
  const CronogramaScreen({super.key});

  @override
  State<CronogramaScreen> createState() => _CronogramaScreenState();
}

class _CronogramaScreenState extends State<CronogramaScreen> {
  List<CronogramaFila> _filas = [];
  bool _loading = true;
  String? _error;
  int _anio = DateTime.now().year;

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  Future<void> _cargar() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final data = await BibliotecaService(ApiClient())
          .cronograma(anio: _anio);
      setState(() => _filas = data);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Cronograma'),
        actions: [
          IconButton(
            icon: const Icon(Icons.chevron_left),
            onPressed: () {
              setState(() => _anio--);
              _cargar();
            },
          ),
          TextButton(
            onPressed: () {
              setState(() => _anio = DateTime.now().year);
              _cargar();
            },
            child: Text('$_anio',
                style: const TextStyle(fontWeight: FontWeight.bold)),
          ),
          IconButton(
            icon: const Icon(Icons.chevron_right),
            onPressed: () {
              setState(() => _anio++);
              _cargar();
            },
          ),
          IconButton(icon: const Icon(Icons.refresh), onPressed: _cargar),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? AppError(message: _error!, onRetry: _cargar)
              : _filas.isEmpty
                  ? const Center(
                      child: Text('No hay programas activos'))
                  : _buildTable(),
    );
  }

  Widget _buildTable() {
    const meses = [
      'E', 'F', 'M', 'A', 'M', 'J',
      'J', 'A', 'S', 'O', 'N', 'D'
    ];
    final mesActual = DateTime.now().month;
    final anioActual = DateTime.now().year;

    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: SingleChildScrollView(
        child: DataTable(
          columnSpacing: 4,
          horizontalMargin: 12,
          headingRowHeight: 36,
          dataRowMinHeight: 36,
          dataRowMaxHeight: 48,
          columns: [
            const DataColumn(
                label: SizedBox(
                    width: 160,
                    child: Text('Programa',
                        style:
                            TextStyle(fontWeight: FontWeight.bold)))),
            ...List.generate(
              12,
              (i) => DataColumn(
                label: Container(
                  width: 28,
                  alignment: Alignment.center,
                  decoration: (_anio == anioActual &&
                          i + 1 == mesActual)
                      ? BoxDecoration(
                          color: Theme.of(context)
                              .colorScheme
                              .primaryContainer,
                          borderRadius: BorderRadius.circular(4),
                        )
                      : null,
                  child: Text(meses[i],
                      style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 12)),
                ),
              ),
            ),
          ],
          rows: _filas
              .map(
                (f) => DataRow(
                  cells: [
                    DataCell(
                      SizedBox(
                        width: 160,
                        child: Text(
                          f.etiqueta,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(fontSize: 12),
                        ),
                      ),
                    ),
                    ...List.generate(
                      12,
                      (i) {
                        final estado = f.meses['${i + 1}'];
                        return DataCell(
                          Center(child: _CeldaMes(estado)),
                        );
                      },
                    ),
                  ],
                ),
              )
              .toList(),
        ),
      ),
    );
  }
}

class _CeldaMes extends StatelessWidget {
  final String? estado;
  const _CeldaMes(this.estado);

  @override
  Widget build(BuildContext context) {
    if (estado == null) return const SizedBox(width: 28);
    final (color, icon) = switch (estado) {
      'completada' => (const Color(0xFF0E6B52), Icons.check),
      'activa' => (Colors.blue, Icons.pending),
      'planned' => (Colors.orange, Icons.schedule),
      _ => (Colors.grey, Icons.circle),
    };
    return Container(
      width: 24,
      height: 24,
      decoration: BoxDecoration(
        color: color.withOpacity(0.2),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: color.withOpacity(0.5)),
      ),
      child: Icon(icon, size: 14, color: color),
    );
  }
}
