import 'package:flutter/material.dart';
import '../../core/api_client.dart';
import '../../models/repuesto.dart';
import '../../services/admin_service.dart';
import '../../widgets/app_error.dart';

class AdminRepuestosScreen extends StatefulWidget {
  const AdminRepuestosScreen({super.key});

  @override
  State<AdminRepuestosScreen> createState() => _AdminRepuestosScreenState();
}

class _AdminRepuestosScreenState extends State<AdminRepuestosScreen> {
  late final AdminService _svc;
  List<AdminRepuestoItem> _items = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _svc = AdminService(ApiClient());
    _cargar();
  }

  Future<void> _cargar() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final data = await _svc.listarRepuestos();
      setState(() => _items = data);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _mostrarForm([AdminRepuestoItem? item]) async {
    final result = await showDialog<Map<String, dynamic>>(
      context: context,
      builder: (_) => _RepuestoDialog(item: item),
    );
    if (result == null) return;
    try {
      if (item == null) {
        await _svc.crearRepuesto(result);
      } else {
        await _svc.actualizarRepuesto(item.id, result);
      }
      _cargar();
    } catch (e) {
      if (mounted) showError(context, e);
    }
  }

  Future<void> _eliminar(AdminRepuestoItem item) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Eliminar repuesto'),
        content: Text('¿Eliminar "${item.nombre}"?'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Cancelar')),
          FilledButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Eliminar')),
        ],
      ),
    );
    if (ok != true) return;
    try {
      await _svc.eliminarRepuesto(item.id);
      _cargar();
    } catch (e) {
      if (mounted) showError(context, e);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Repuestos'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _cargar),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _mostrarForm(),
        child: const Icon(Icons.add),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? AppError(message: _error!, onRetry: _cargar)
              : ListView.builder(
                  itemCount: _items.length,
                  itemBuilder: (_, i) {
                    final r = _items[i];
                    return ListTile(
                      leading: CircleAvatar(
                        backgroundColor: r.stockBajo
                            ? Colors.orange.shade100
                            : Theme.of(context)
                                .colorScheme
                                .primaryContainer,
                        child: Icon(Icons.inventory_2,
                            size: 20,
                            color: r.stockBajo
                                ? Colors.orange.shade700
                                : Theme.of(context).colorScheme.primary),
                      ),
                      title: Text(r.nombre),
                      subtitle: Text(
                          'Stock: ${r.stockActual} / Mín: ${r.stockMinimo}${!r.activo ? ' · Inactivo' : ''}'),
                      trailing: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          if (r.stockBajo)
                            const Icon(Icons.warning_amber,
                                color: Colors.orange, size: 20),
                          IconButton(
                              icon: const Icon(Icons.edit, size: 20),
                              onPressed: () => _mostrarForm(r)),
                          IconButton(
                              icon: const Icon(Icons.delete_outline,
                                  size: 20),
                              onPressed: () => _eliminar(r)),
                        ],
                      ),
                    );
                  },
                ),
    );
  }
}

class _RepuestoDialog extends StatefulWidget {
  final AdminRepuestoItem? item;
  const _RepuestoDialog({this.item});

  @override
  State<_RepuestoDialog> createState() => _RepuestoDialogState();
}

class _RepuestoDialogState extends State<_RepuestoDialog> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _nombreCtrl;
  late final TextEditingController _obsCtrl;
  late final TextEditingController _stockCtrl;
  late final TextEditingController _minCtrl;
  bool _activo = true;

  @override
  void initState() {
    super.initState();
    final i = widget.item;
    _nombreCtrl = TextEditingController(text: i?.nombre ?? '');
    _obsCtrl = TextEditingController(text: i?.observaciones ?? '');
    _stockCtrl =
        TextEditingController(text: i?.stockActual.toString() ?? '0');
    _minCtrl =
        TextEditingController(text: i?.stockMinimo.toString() ?? '0');
    _activo = i?.activo ?? true;
  }

  @override
  void dispose() {
    for (final c in [_nombreCtrl, _obsCtrl, _stockCtrl, _minCtrl]) {
      c.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(widget.item == null ? 'Nuevo repuesto' : 'Editar repuesto'),
      content: SizedBox(
        width: 400,
        child: Form(
          key: _formKey,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextFormField(
                  controller: _nombreCtrl,
                  validator: (v) =>
                      (v?.trim().isEmpty ?? true) ? 'Requerido' : null,
                  decoration: const InputDecoration(
                      labelText: 'Nombre *',
                      border: OutlineInputBorder(),
                      isDense: true),
                ),
                const SizedBox(height: 10),
                TextFormField(
                  controller: _obsCtrl,
                  maxLines: 2,
                  decoration: const InputDecoration(
                      labelText: 'Observaciones',
                      border: OutlineInputBorder(),
                      isDense: true),
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    Expanded(
                      child: TextFormField(
                        controller: _stockCtrl,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(
                            labelText: 'Stock actual',
                            border: OutlineInputBorder(),
                            isDense: true),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: TextFormField(
                        controller: _minCtrl,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(
                            labelText: 'Stock mínimo',
                            border: OutlineInputBorder(),
                            isDense: true),
                      ),
                    ),
                  ],
                ),
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Activo'),
                  value: _activo,
                  onChanged: (v) => setState(() => _activo = v),
                ),
              ],
            ),
          ),
        ),
      ),
      actions: [
        TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancelar')),
        FilledButton(
          onPressed: () {
            if (!_formKey.currentState!.validate()) return;
            Navigator.pop(context, {
              'nombre': _nombreCtrl.text.trim(),
              'observaciones': _obsCtrl.text.trim(),
              'stock_actual':
                  double.tryParse(_stockCtrl.text) ?? 0,
              'stock_minimo': double.tryParse(_minCtrl.text) ?? 0,
              'activo': _activo,
            });
          },
          child: const Text('Guardar'),
        ),
      ],
    );
  }
}
