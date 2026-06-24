import 'package:flutter/material.dart';
import '../../core/api_client.dart';
import '../../models/equipo.dart';
import '../../services/admin_service.dart';
import '../../widgets/app_error.dart';

class AdminEquiposScreen extends StatefulWidget {
  const AdminEquiposScreen({super.key});

  @override
  State<AdminEquiposScreen> createState() => _AdminEquiposScreenState();
}

class _AdminEquiposScreenState extends State<AdminEquiposScreen> {
  late final AdminService _svc;
  List<AdminEquipoItem> _equipos = [];
  List<TipoEquipoItem> _tipos = [];
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
      final results = await Future.wait([
        _svc.listarEquipos(),
        _svc.listarTipos(),
      ]);
      setState(() {
        _equipos = results[0] as List<AdminEquipoItem>;
        _tipos = results[1] as List<TipoEquipoItem>;
      });
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _mostrarForm([AdminEquipoItem? item]) async {
    final result = await showDialog<Map<String, dynamic>>(
      context: context,
      builder: (_) => _EquipoDialog(item: item, tipos: _tipos),
    );
    if (result == null) return;
    try {
      if (item == null) {
        await _svc.crearEquipo(result);
      } else {
        await _svc.actualizarEquipo(item.id, result);
      }
      _cargar();
    } catch (e) {
      if (mounted) showError(context, e);
    }
  }

  Future<void> _eliminar(AdminEquipoItem item) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Eliminar equipo'),
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
      await _svc.eliminarEquipo(item.id);
      _cargar();
    } catch (e) {
      if (mounted) showError(context, e);
    }
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
      floatingActionButton: FloatingActionButton(
        onPressed: () => _mostrarForm(),
        child: const Icon(Icons.add),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? AppError(message: _error!, onRetry: _cargar)
              : ListView.builder(
                  itemCount: _equipos.length,
                  itemBuilder: (_, i) {
                    final e = _equipos[i];
                    return ListTile(
                      title: Text(e.nombre),
                      subtitle: Text(
                          '${e.tipoNombre}${e.ubicacion.isNotEmpty ? ' · ${e.ubicacion}' : ''}'),
                      leading: CircleAvatar(
                        backgroundColor: e.activo
                            ? Theme.of(context).colorScheme.primaryContainer
                            : Colors.grey.shade200,
                        child: Icon(Icons.precision_manufacturing,
                            size: 20,
                            color: e.activo
                                ? Theme.of(context).colorScheme.primary
                                : Colors.grey),
                      ),
                      trailing: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          IconButton(
                              icon: const Icon(Icons.edit, size: 20),
                              onPressed: () => _mostrarForm(e)),
                          IconButton(
                              icon: const Icon(Icons.delete_outline,
                                  size: 20),
                              onPressed: () => _eliminar(e)),
                        ],
                      ),
                    );
                  },
                ),
    );
  }
}

class _EquipoDialog extends StatefulWidget {
  final AdminEquipoItem? item;
  final List<TipoEquipoItem> tipos;
  const _EquipoDialog({this.item, required this.tipos});

  @override
  State<_EquipoDialog> createState() => _EquipoDialogState();
}

class _EquipoDialogState extends State<_EquipoDialog> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _nombreCtrl;
  late final TextEditingController _serieCtrl;
  late final TextEditingController _marcaCtrl;
  late final TextEditingController _modeloCtrl;
  late final TextEditingController _ubicCtrl;
  late final TextEditingController _obsCtrl;
  late final TextEditingController _horasActualesCtrl;
  int? _tipoId;
  bool _activo = true;
  bool _horasTrabajoActivo = false;

  @override
  void initState() {
    super.initState();
    final i = widget.item;
    _nombreCtrl = TextEditingController(text: i?.nombre ?? '');
    _serieCtrl = TextEditingController(text: i?.numeroSerie ?? '');
    _marcaCtrl = TextEditingController(text: i?.marca ?? '');
    _modeloCtrl = TextEditingController(text: i?.modelo ?? '');
    _ubicCtrl = TextEditingController(text: i?.ubicacion ?? '');
    _obsCtrl = TextEditingController(text: i?.observaciones ?? '');
    _horasActualesCtrl =
        TextEditingController(text: (i?.horasTrabajoActual ?? 0).toString());
    _tipoId = i?.tipoId;
    _activo = i?.activo ?? true;
    _horasTrabajoActivo = i?.horasTrabajoActivo ?? false;
  }

  @override
  void dispose() {
    for (final c in [
      _nombreCtrl,
      _serieCtrl,
      _marcaCtrl,
      _modeloCtrl,
      _ubicCtrl,
      _obsCtrl,
      _horasActualesCtrl,
    ]) {
      c.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(
          widget.item == null ? 'Nuevo equipo' : 'Editar equipo'),
      content: SizedBox(
        width: 400,
        child: Form(
          key: _formKey,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                _field(_nombreCtrl, 'Nombre *',
                    validator: (v) => (v == null || v.trim().isEmpty)
                        ? 'Requerido'
                        : null),
                const SizedBox(height: 10),
                DropdownButtonFormField<int?>(
                  value: _tipoId,
                  hint: const Text('Tipo de equipo'),
                  items: [
                    const DropdownMenuItem(
                        value: null, child: Text('Sin tipo')),
                    ...widget.tipos.map((t) => DropdownMenuItem(
                        value: t.id, child: Text(t.nombre))),
                  ],
                  onChanged: (v) => setState(() => _tipoId = v),
                  decoration: const InputDecoration(
                      border: OutlineInputBorder(), isDense: true),
                ),
                const SizedBox(height: 10),
                _field(_marcaCtrl, 'Marca'),
                const SizedBox(height: 10),
                _field(_modeloCtrl, 'Modelo'),
                const SizedBox(height: 10),
                _field(_serieCtrl, 'Nro. serie'),
                const SizedBox(height: 10),
                _field(_ubicCtrl, 'Ubicación'),
                const SizedBox(height: 10),
                _field(_obsCtrl, 'Observaciones', maxLines: 2),
                const SizedBox(height: 6),
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Activo'),
                  value: _activo,
                  onChanged: (v) => setState(() => _activo = v),
                ),
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Controlar horas de trabajo'),
                  value: _horasTrabajoActivo,
                  onChanged: (v) => setState(() => _horasTrabajoActivo = v),
                ),
                if (_horasTrabajoActivo) ...[
                  const SizedBox(height: 10),
                  TextFormField(
                    controller: _horasActualesCtrl,
                    keyboardType: const TextInputType.numberWithOptions(
                        decimal: true),
                    decoration: const InputDecoration(
                        labelText: 'Horas actuales',
                        border: OutlineInputBorder(),
                        isDense: true),
                  ),
                ],
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
              'tipo_id': _tipoId,
              'numero_serie': _serieCtrl.text.trim(),
              'marca': _marcaCtrl.text.trim(),
              'modelo': _modeloCtrl.text.trim(),
              'ubicacion': _ubicCtrl.text.trim(),
              'fecha_adquisicion': widget.item?.fechaAdquisicion ?? '',
              'observaciones': _obsCtrl.text.trim(),
              'activo': _activo,
              'horas_trabajo_activo': _horasTrabajoActivo,
              'horas_trabajo_actual':
                  double.tryParse(_horasActualesCtrl.text) ?? 0.0,
            });
          },
          child: const Text('Guardar'),
        ),
      ],
    );
  }

  Widget _field(TextEditingController ctrl, String label,
      {int maxLines = 1,
      String? Function(String?)? validator}) {
    return TextFormField(
      controller: ctrl,
      maxLines: maxLines,
      validator: validator,
      decoration: InputDecoration(
          labelText: label,
          border: const OutlineInputBorder(),
          isDense: true),
    );
  }
}
