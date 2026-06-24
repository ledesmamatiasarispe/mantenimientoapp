import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/api_client.dart';
import '../../core/app_state.dart';
import '../../models/orden.dart';
import '../../services/ordenes_service.dart';
import '../../widgets/estado_chip.dart';
import '../../widgets/app_error.dart';
import 'orden_detail_screen.dart';
import 'crear_orden_screen.dart';

class OrdenesScreen extends StatefulWidget {
  const OrdenesScreen({super.key});

  @override
  State<OrdenesScreen> createState() => _OrdenesScreenState();
}

class _OrdenesScreenState extends State<OrdenesScreen> {
  late final OrdenesService _svc;
  List<OrdenCard> _ordenes = [];
  bool _loading = true;
  String? _error;
  String? _filtroEstado;
  bool _soloMis = false;

  @override
  void initState() {
    super.initState();
    _svc = OrdenesService(ApiClient());
    _cargar();
  }

  Future<void> _cargar() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final data = await _svc.listar(
        estado: _filtroEstado,
        soloMis: _soloMis,
      );
      setState(() => _ordenes = data);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _abrirDetalle(OrdenCard orden) async {
    final actualizada = await Navigator.push<bool>(
      context,
      MaterialPageRoute(
          builder: (_) => OrdenDetailScreen(ordenId: orden.id)),
    );
    if (actualizada == true) _cargar();
  }

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final isAdmin = state.tecnico?.esAdmin ?? false;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Órdenes de trabajo'),
        actions: [
          IconButton(
              icon: const Icon(Icons.refresh), onPressed: _cargar),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () async {
          final created = await Navigator.push<bool>(
            context,
            MaterialPageRoute(
                builder: (_) => const CrearOrdenScreen()),
          );
          if (created == true) _cargar();
        },
        child: const Icon(Icons.add),
      ),
      body: Column(
        children: [
          _Filtros(
            filtroEstado: _filtroEstado,
            soloMis: _soloMis,
            isAdmin: isAdmin,
            onEstado: (v) {
              setState(() => _filtroEstado = v);
              _cargar();
            },
            onSoloMis: (v) {
              setState(() => _soloMis = v);
              _cargar();
            },
          ),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : _error != null
                    ? AppError(message: _error!, onRetry: _cargar)
                    : _ordenes.isEmpty
                        ? const Center(
                            child: Text('No hay órdenes con ese filtro'))
                        : RefreshIndicator(
                            onRefresh: _cargar,
                            child: ListView.builder(
                              itemCount: _ordenes.length,
                              itemBuilder: (_, i) =>
                                  _OrdenTile(_ordenes[i], _abrirDetalle),
                            ),
                          ),
          ),
        ],
      ),
    );
  }
}

class _Filtros extends StatelessWidget {
  final String? filtroEstado;
  final bool soloMis;
  final bool isAdmin;
  final ValueChanged<String?> onEstado;
  final ValueChanged<bool> onSoloMis;

  const _Filtros({
    required this.filtroEstado,
    required this.soloMis,
    required this.isAdmin,
    required this.onEstado,
    required this.onSoloMis,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      child: Row(
        children: [
          Expanded(
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: [
                  _FilterChip('Todas', null, filtroEstado, onEstado),
                  const SizedBox(width: 6),
                  _FilterChip(
                      'Pendiente', 'PENDIENTE', filtroEstado, onEstado),
                  const SizedBox(width: 6),
                  _FilterChip('En progreso', 'EN_PROGRESO', filtroEstado,
                      onEstado),
                  const SizedBox(width: 6),
                  _FilterChip(
                      'Completada', 'COMPLETADA', filtroEstado, onEstado),
                ],
              ),
            ),
          ),
          FilterChip(
            label: const Text('Mis órdenes'),
            selected: soloMis,
            onSelected: onSoloMis,
          ),
        ],
      ),
    );
  }
}

class _FilterChip extends StatelessWidget {
  final String label;
  final String? value;
  final String? selected;
  final ValueChanged<String?> onTap;

  const _FilterChip(this.label, this.value, this.selected, this.onTap);

  @override
  Widget build(BuildContext context) {
    return FilterChip(
      label: Text(label),
      selected: selected == value,
      onSelected: (_) => onTap(value),
    );
  }
}

class _OrdenTile extends StatelessWidget {
  final OrdenCard orden;
  final Future<void> Function(OrdenCard) onTap;

  const _OrdenTile(this.orden, this.onTap);

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      child: ListTile(
        onTap: () => onTap(orden),
        title: Text(
          '${orden.equipoNombre} — #${orden.id}',
          style: const TextStyle(fontWeight: FontWeight.w600),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (orden.descripcion.isNotEmpty)
              Text(orden.descripcion,
                  maxLines: 1, overflow: TextOverflow.ellipsis),
            const SizedBox(height: 4),
            Row(
              children: [
                TipoChip(orden.tipo),
                const SizedBox(width: 8),
                EstadoChip(orden.estado),
              ],
            ),
            if (orden.tecnicoNombre.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 2),
                child: Text(orden.tecnicoNombre,
                    style: Theme.of(context).textTheme.bodySmall),
              ),
          ],
        ),
        trailing: Text(
          orden.fechaApertura,
          style: Theme.of(context).textTheme.bodySmall,
        ),
        isThreeLine: true,
      ),
    );
  }
}
