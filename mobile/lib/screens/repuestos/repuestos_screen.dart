import 'package:flutter/material.dart';
import '../../core/api_client.dart';
import '../../models/repuesto.dart';
import '../../services/biblioteca_service.dart';
import '../../widgets/app_error.dart';

class RepuestosScreen extends StatefulWidget {
  const RepuestosScreen({super.key});

  @override
  State<RepuestosScreen> createState() => _RepuestosScreenState();
}

class _RepuestosScreenState extends State<RepuestosScreen> {
  List<RepuestoDisponible> _repuestos = [];
  bool _loading = true;
  String? _error;
  String _busqueda = '';
  bool _soloStockBajo = false;

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
          await BibliotecaService(ApiClient()).listarRepuestos();
      setState(() => _repuestos = data);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  List<RepuestoDisponible> get _filtrados {
    var lista = _repuestos;
    if (_soloStockBajo) lista = lista.where((r) => r.stockBajo).toList();
    if (_busqueda.isNotEmpty) {
      final q = _busqueda.toLowerCase();
      lista = lista.where((r) => r.nombre.toLowerCase().contains(q)).toList();
    }
    return lista;
  }

  @override
  Widget build(BuildContext context) {
    final stockBajoCount = _repuestos.where((r) => r.stockBajo).length;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Repuestos'),
        actions: [
          if (stockBajoCount > 0)
            Badge(
              label: Text('$stockBajoCount'),
              child: IconButton(
                icon: Icon(
                  Icons.warning_amber,
                  color: _soloStockBajo ? Colors.orange : null,
                ),
                onPressed: () =>
                    setState(() => _soloStockBajo = !_soloStockBajo),
                tooltip: 'Stock bajo',
              ),
            ),
          IconButton(icon: const Icon(Icons.refresh), onPressed: _cargar),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: TextField(
              decoration: const InputDecoration(
                hintText: 'Buscar repuesto...',
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
                              _RepuestoTile(_filtrados[i]),
                        ),
                      ),
          ),
        ],
      ),
    );
  }
}

class _RepuestoTile extends StatelessWidget {
  final RepuestoDisponible r;
  const _RepuestoTile(this.r);

  @override
  Widget build(BuildContext context) {
    final stockBajo = r.stockBajo;
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: stockBajo
              ? Colors.orange.shade100
              : Theme.of(context).colorScheme.primaryContainer,
          child: Icon(
            Icons.inventory_2,
            color: stockBajo
                ? Colors.orange.shade700
                : Theme.of(context).colorScheme.primary,
          ),
        ),
        title: Text(r.nombre,
            style: const TextStyle(fontWeight: FontWeight.w600)),
        subtitle: Text(
          'Stock: ${r.stockActual}${r.stockMinimo > 0 ? ' / Mín: ${r.stockMinimo}' : ''}',
          style: TextStyle(
              color: stockBajo ? Colors.orange.shade700 : null),
        ),
        trailing: stockBajo
            ? const Icon(Icons.warning_amber, color: Colors.orange)
            : null,
      ),
    );
  }
}
