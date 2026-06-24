import 'package:flutter/material.dart';
import '../../core/api_client.dart';
import '../../models/equipo.dart';
import '../../services/admin_service.dart';
import '../../widgets/app_error.dart';

class AdminProgramasScreen extends StatefulWidget {
  const AdminProgramasScreen({super.key});

  @override
  State<AdminProgramasScreen> createState() => _AdminProgramasScreenState();
}

class _AdminProgramasScreenState extends State<AdminProgramasScreen> {
  late final AdminService _svc;
  List<AdminProgramaItem> _programas = [];
  List<AdminEquipoItem> _equipos = [];
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
        _svc.listarProgramas(),
        _svc.listarEquipos(),
      ]);
      setState(() {
        _programas = results[0] as List<AdminProgramaItem>;
        _equipos = results[1] as List<AdminEquipoItem>;
      });
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _mostrarForm([AdminProgramaItem? item]) async {
    final result = await showDialog<Map<String, dynamic>>(
      context: context,
      builder: (_) => _ProgramaDialog(item: item, equipos: _equipos),
    );
    if (result == null) return;
    try {
      if (item == null) {
        await _svc.crearPrograma(result);
      } else {
        await _svc.actualizarPrograma(item.id, result);
      }
      _cargar();
    } catch (e) {
      if (mounted) showError(context, e);
    }
  }

  Future<void> _verPasos(AdminProgramaItem programa) async {
    await Navigator.push(
      context,
      MaterialPageRoute(
          builder: (_) => _PasosScreen(
                programaId: programa.id,
                titulo: programa.descripcion,
                svc: _svc,
              )),
    );
  }

  Future<void> _eliminar(AdminProgramaItem item) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Eliminar programa'),
        content: Text('¿Eliminar "${item.descripcion}"?'),
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
      await _svc.eliminarPrograma(item.id);
      _cargar();
    } catch (e) {
      if (mounted) showError(context, e);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Programas de mantenimiento'),
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
                  itemCount: _programas.length,
                  itemBuilder: (_, i) {
                    final p = _programas[i];
                    return ListTile(
                      title: Text(p.descripcion),
                      subtitle: Text(
                          '${p.equipoNombre} · c/ ${p.frecuenciaMeses} meses'),
                      trailing: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          IconButton(
                              icon: const Icon(Icons.checklist, size: 20),
                              tooltip: 'Pasos',
                              onPressed: () => _verPasos(p)),
                          IconButton(
                              icon: const Icon(Icons.edit, size: 20),
                              onPressed: () => _mostrarForm(p)),
                          IconButton(
                              icon: const Icon(Icons.delete_outline,
                                  size: 20),
                              onPressed: () => _eliminar(p)),
                        ],
                      ),
                    );
                  },
                ),
    );
  }
}

class _ProgramaDialog extends StatefulWidget {
  final AdminProgramaItem? item;
  final List<AdminEquipoItem> equipos;
  const _ProgramaDialog({this.item, required this.equipos});

  @override
  State<_ProgramaDialog> createState() => _ProgramaDialogState();
}

class _ProgramaDialogState extends State<_ProgramaDialog> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _descCtrl;
  late final TextEditingController _freqCtrl;
  late final TextEditingController _ultiCtrl;
  int? _equipoId;
  bool _activo = true;

  @override
  void initState() {
    super.initState();
    final i = widget.item;
    _descCtrl = TextEditingController(text: i?.descripcion ?? '');
    _freqCtrl =
        TextEditingController(text: i?.frecuenciaMeses.toString() ?? '12');
    _ultiCtrl =
        TextEditingController(text: i?.ultimaEjecucion ?? '');
    _equipoId = i?.equipoId;
    _activo = i?.activo ?? true;
  }

  @override
  void dispose() {
    _descCtrl.dispose();
    _freqCtrl.dispose();
    _ultiCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(
          widget.item == null ? 'Nuevo programa' : 'Editar programa'),
      content: SizedBox(
        width: 400,
        child: Form(
          key: _formKey,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                DropdownButtonFormField<int>(
                  value: _equipoId,
                  hint: const Text('Seleccionar equipo'),
                  items: widget.equipos
                      .map((e) => DropdownMenuItem(
                          value: e.id,
                          child: Text(e.nombre,
                              overflow: TextOverflow.ellipsis)))
                      .toList(),
                  onChanged: (v) => setState(() => _equipoId = v),
                  validator: (v) => v == null ? 'Requerido' : null,
                  decoration: const InputDecoration(
                      labelText: 'Equipo *',
                      border: OutlineInputBorder(),
                      isDense: true),
                ),
                const SizedBox(height: 10),
                TextFormField(
                  controller: _descCtrl,
                  validator: (v) =>
                      (v?.trim().isEmpty ?? true) ? 'Requerido' : null,
                  decoration: const InputDecoration(
                      labelText: 'Descripción *',
                      border: OutlineInputBorder(),
                      isDense: true),
                ),
                const SizedBox(height: 10),
                TextFormField(
                  controller: _freqCtrl,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                      labelText: 'Frecuencia (meses)',
                      border: OutlineInputBorder(),
                      isDense: true),
                ),
                const SizedBox(height: 10),
                TextFormField(
                  controller: _ultiCtrl,
                  decoration: const InputDecoration(
                      labelText: 'Última ejecución (YYYY-MM-DD)',
                      border: OutlineInputBorder(),
                      isDense: true),
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
              'equipo_id': _equipoId,
              'descripcion': _descCtrl.text.trim(),
              'frecuencia_meses':
                  int.tryParse(_freqCtrl.text) ?? 12,
              'ultima_ejecucion': _ultiCtrl.text.trim(),
              'activo': _activo,
            });
          },
          child: const Text('Guardar'),
        ),
      ],
    );
  }
}

class _PasosScreen extends StatefulWidget {
  final int programaId;
  final String titulo;
  final AdminService svc;
  const _PasosScreen(
      {required this.programaId,
      required this.titulo,
      required this.svc});

  @override
  State<_PasosScreen> createState() => _PasosScreenState();
}

class _PasosScreenState extends State<_PasosScreen> {
  List<AdminPasoItem> _pasos = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  Future<void> _cargar() async {
    setState(() => _loading = true);
    try {
      final data = await widget.svc.listarPasos(widget.programaId);
      setState(() => _pasos = data);
    } catch (e) {
      if (mounted) showError(context, e);
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _agregarPaso() async {
    final ctrl = TextEditingController();
    final obsCtrl = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Nuevo paso'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: ctrl,
              autofocus: true,
              decoration: const InputDecoration(
                  labelText: 'Descripción *',
                  border: OutlineInputBorder()),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: obsCtrl,
              decoration: const InputDecoration(
                  labelText: 'Observaciones',
                  border: OutlineInputBorder()),
            ),
          ],
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Cancelar')),
          FilledButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Crear')),
        ],
      ),
    );
    if (ok != true || ctrl.text.trim().isEmpty) return;
    try {
      await widget.svc
          .crearPaso(widget.programaId, ctrl.text.trim(), obsCtrl.text.trim());
      _cargar();
    } catch (e) {
      if (mounted) showError(context, e);
    }
  }

  Future<void> _eliminarPaso(AdminPasoItem paso) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Eliminar paso'),
        content: Text('¿Eliminar "${paso.descripcion}"?'),
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
      await widget.svc.eliminarPaso(widget.programaId, paso.id);
      _cargar();
    } catch (e) {
      if (mounted) showError(context, e);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.titulo, overflow: TextOverflow.ellipsis),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _cargar),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _agregarPaso,
        child: const Icon(Icons.add),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _pasos.isEmpty
              ? const Center(child: Text('Sin pasos definidos'))
              : ReorderableListView.builder(
                  itemCount: _pasos.length,
                  onReorder: (_, __) {},
                  itemBuilder: (_, i) {
                    final p = _pasos[i];
                    return ListTile(
                      key: ValueKey(p.id),
                      leading: CircleAvatar(
                        radius: 14,
                        child: Text('${p.posicion}',
                            style: const TextStyle(fontSize: 12)),
                      ),
                      title: Text(p.descripcion),
                      subtitle: p.observaciones.isNotEmpty
                          ? Text(p.observaciones,
                              style: const TextStyle(fontSize: 12))
                          : null,
                      trailing: IconButton(
                          icon: const Icon(Icons.delete_outline, size: 20),
                          onPressed: () => _eliminarPaso(p)),
                    );
                  },
                ),
    );
  }
}
