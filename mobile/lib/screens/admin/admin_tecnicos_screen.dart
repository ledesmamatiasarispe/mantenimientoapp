import 'package:flutter/material.dart';
import '../../core/api_client.dart';
import '../../models/tecnico.dart';
import '../../services/admin_service.dart';
import '../../widgets/app_error.dart';

class AdminTecnicosScreen extends StatefulWidget {
  const AdminTecnicosScreen({super.key});

  @override
  State<AdminTecnicosScreen> createState() => _AdminTecnicosScreenState();
}

class _AdminTecnicosScreenState extends State<AdminTecnicosScreen> {
  late final AdminService _svc;
  List<AdminTecnicoItem> _tecnicos = [];
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
      setState(() => _tecnicos = []);
      final data = await _svc.listarTecnicos();
      setState(() => _tecnicos = data);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _mostrarForm([AdminTecnicoItem? item]) async {
    final result = await showDialog<Map<String, dynamic>>(
      context: context,
      builder: (_) => _TecnicoDialog(item: item),
    );
    if (result == null) return;
    try {
      if (item == null) {
        await _svc.crearTecnico(result);
      } else {
        await _svc.actualizarTecnico(item.id, result);
      }
      _cargar();
    } catch (e) {
      if (mounted) showError(context, e);
    }
  }

  Future<void> _cambiarPassword(AdminTecnicoItem item) async {
    final ctrl = TextEditingController();
    final pass = await showDialog<String>(
      context: context,
      builder: (_) => AlertDialog(
        title: Text('Cambiar contraseña\n${item.nombreCompleto}'),
        content: TextField(
          controller: ctrl,
          obscureText: true,
          autofocus: true,
          decoration: const InputDecoration(
              labelText: 'Nueva contraseña',
              border: OutlineInputBorder()),
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancelar')),
          FilledButton(
              onPressed: () => Navigator.pop(context, ctrl.text),
              child: const Text('Cambiar')),
        ],
      ),
    );
    if (pass == null || pass.isEmpty) return;
    try {
      await _svc.cambiarPassword(item.id, pass);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Contraseña actualizada')),
        );
      }
    } catch (e) {
      if (mounted) showError(context, e);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Técnicos'),
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
                  itemCount: _tecnicos.length,
                  itemBuilder: (_, i) {
                    final t = _tecnicos[i];
                    return ListTile(
                      leading: CircleAvatar(
                        backgroundColor: t.activo
                            ? Theme.of(context)
                                .colorScheme
                                .primaryContainer
                            : Colors.grey.shade200,
                        child: Text(
                          t.nombre.isNotEmpty
                              ? t.nombre[0].toUpperCase()
                              : '?',
                          style: TextStyle(
                            color: t.activo
                                ? Theme.of(context).colorScheme.primary
                                : Colors.grey,
                          ),
                        ),
                      ),
                      title: Text(t.nombreCompleto),
                      subtitle: Text(
                          'Legajo: ${t.legajo}${t.especialidad.isNotEmpty ? ' · ${t.especialidad}' : ''}'),
                      trailing: PopupMenuButton<String>(
                        onSelected: (action) {
                          if (action == 'edit') _mostrarForm(t);
                          if (action == 'pass') _cambiarPassword(t);
                        },
                        itemBuilder: (_) => const [
                          PopupMenuItem(
                              value: 'edit', child: Text('Editar')),
                          PopupMenuItem(
                              value: 'pass',
                              child: Text('Cambiar contraseña')),
                        ],
                      ),
                    );
                  },
                ),
    );
  }
}

class _TecnicoDialog extends StatefulWidget {
  final AdminTecnicoItem? item;
  const _TecnicoDialog({this.item});

  @override
  State<_TecnicoDialog> createState() => _TecnicoDialogState();
}

class _TecnicoDialogState extends State<_TecnicoDialog> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _nombreCtrl;
  late final TextEditingController _apellidoCtrl;
  late final TextEditingController _legajoCtrl;
  late final TextEditingController _telCtrl;
  late final TextEditingController _espCtrl;
  late final TextEditingController _passCtrl;
  bool _activo = true;

  @override
  void initState() {
    super.initState();
    final i = widget.item;
    _nombreCtrl = TextEditingController(text: i?.nombre ?? '');
    _apellidoCtrl = TextEditingController(text: i?.apellido ?? '');
    _legajoCtrl = TextEditingController(text: i?.legajo ?? '');
    _telCtrl = TextEditingController(text: i?.telefono ?? '');
    _espCtrl = TextEditingController(text: i?.especialidad ?? '');
    _passCtrl = TextEditingController();
    _activo = i?.activo ?? true;
  }

  @override
  void dispose() {
    for (final c in [
      _nombreCtrl,
      _apellidoCtrl,
      _legajoCtrl,
      _telCtrl,
      _espCtrl,
      _passCtrl
    ]) {
      c.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isNew = widget.item == null;
    return AlertDialog(
      title: Text(isNew ? 'Nuevo técnico' : 'Editar técnico'),
      content: SizedBox(
        width: 400,
        child: Form(
          key: _formKey,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                _field(_nombreCtrl, 'Nombre *',
                    validator: (v) =>
                        (v?.trim().isEmpty ?? true) ? 'Requerido' : null),
                const SizedBox(height: 10),
                _field(_apellidoCtrl, 'Apellido *',
                    validator: (v) =>
                        (v?.trim().isEmpty ?? true) ? 'Requerido' : null),
                const SizedBox(height: 10),
                _field(_legajoCtrl, 'Legajo *',
                    validator: (v) =>
                        (v?.trim().isEmpty ?? true) ? 'Requerido' : null),
                const SizedBox(height: 10),
                _field(_telCtrl, 'Teléfono'),
                const SizedBox(height: 10),
                _field(_espCtrl, 'Especialidad'),
                if (isNew) ...[
                  const SizedBox(height: 10),
                  TextFormField(
                    controller: _passCtrl,
                    obscureText: true,
                    validator: (v) =>
                        (v?.isEmpty ?? true) ? 'Requerido' : null,
                    decoration: const InputDecoration(
                        labelText: 'Contraseña *',
                        border: OutlineInputBorder(),
                        isDense: true),
                  ),
                ],
                if (!isNew)
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
            final body = <String, dynamic>{
              'nombre': _nombreCtrl.text.trim(),
              'apellido': _apellidoCtrl.text.trim(),
              'legajo': _legajoCtrl.text.trim(),
              'telefono': _telCtrl.text.trim(),
              'especialidad': _espCtrl.text.trim(),
              'activo': _activo,
            };
            if (isNew) body['password'] = _passCtrl.text;
            Navigator.pop(context, body);
          },
          child: const Text('Guardar'),
        ),
      ],
    );
  }

  Widget _field(TextEditingController ctrl, String label,
      {String? Function(String?)? validator}) {
    return TextFormField(
      controller: ctrl,
      validator: validator,
      decoration: InputDecoration(
          labelText: label,
          border: const OutlineInputBorder(),
          isDense: true),
    );
  }
}
