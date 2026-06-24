import 'package:flutter/material.dart';
import '../../core/api_client.dart';
import '../../models/equipo.dart';
import '../../services/biblioteca_service.dart';
import '../../widgets/app_error.dart';

class EquiposScreen extends StatefulWidget {
  const EquiposScreen({super.key});

  @override
  State<EquiposScreen> createState() => _EquiposScreenState();
}

class _EquiposScreenState extends State<EquiposScreen> {
  List<EquipoCard> _equipos = [];
  bool _loading = true;
  String? _error;
  String _busqueda = '';

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
      final data =
          await BibliotecaService(ApiClient()).listarEquipos();
      setState(() => _equipos = data);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  List<EquipoCard> get _filtrados {
    if (_busqueda.isEmpty) return _equipos;
    final q = _busqueda.toLowerCase();
    return _equipos
        .where((e) =>
            e.nombre.toLowerCase().contains(q) ||
            e.ubicacion.toLowerCase().contains(q) ||
            e.marca.toLowerCase().contains(q))
        .toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Equipos'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _cargar),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: TextField(
              decoration: const InputDecoration(
                hintText: 'Buscar equipo...',
                prefixIcon: Icon(Icons.search),
                border: OutlineInputBorder(),
                isDense: true,
              ),
              onChanged: (v) => setState(() => _busqueda = v),
            ),
          ),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : _error != null
                    ? AppError(message: _error!, onRetry: _cargar)
                    : RefreshIndicator(
                        onRefresh: _cargar,
                        child: ListView.builder(
                          itemCount: _filtrados.length,
                          itemBuilder: (_, i) =>
                              _EquipoTile(_filtrados[i]),
                        ),
                      ),
          ),
        ],
      ),
    );
  }
}

class _EquipoTile extends StatelessWidget {
  final EquipoCard equipo;
  const _EquipoTile(this.equipo);

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor:
              Theme.of(context).colorScheme.primaryContainer,
          child: Icon(Icons.precision_manufacturing,
              color: Theme.of(context).colorScheme.primary),
        ),
        title: Text(equipo.nombre,
            style: const TextStyle(fontWeight: FontWeight.w600)),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (equipo.tipoNombre.isNotEmpty) Text(equipo.tipoNombre),
            if (equipo.ubicacion.isNotEmpty)
              Row(children: [
                const Icon(Icons.location_on, size: 12),
                const SizedBox(width: 2),
                Text(equipo.ubicacion,
                    style: const TextStyle(fontSize: 12)),
              ]),
            if (equipo.marca.isNotEmpty || equipo.modelo.isNotEmpty)
              Text(
                  '${equipo.marca} ${equipo.modelo}'.trim(),
                  style: const TextStyle(fontSize: 12)),
          ],
        ),
        trailing: equipo.programasActivosCount > 0
            ? Chip(
                label:
                    Text('${equipo.programasActivosCount} prog.'),
                backgroundColor:
                    Theme.of(context).colorScheme.secondaryContainer,
                padding: EdgeInsets.zero,
                visualDensity: VisualDensity.compact,
              )
            : null,
        isThreeLine: true,
      ),
    );
  }
}
