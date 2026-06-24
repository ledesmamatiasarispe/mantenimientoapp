import 'package:flutter/material.dart';
import '../../core/api_client.dart';
import '../../models/equipo.dart';
import '../../services/ordenes_service.dart';
import '../../services/biblioteca_service.dart';
import '../../widgets/app_error.dart';

class CrearOrdenScreen extends StatefulWidget {
  const CrearOrdenScreen({super.key});

  @override
  State<CrearOrdenScreen> createState() => _CrearOrdenScreenState();
}

class _CrearOrdenScreenState extends State<CrearOrdenScreen> {
  final _formKey = GlobalKey<FormState>();
  List<EquipoCard> _equipos = [];
  EquipoCard? _equipoSel;
  String _tipo = 'CORRECTIVO';
  final _descCtrl = TextEditingController();
  final _obsCtrl = TextEditingController();
  bool _loading = true;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _cargarEquipos();
  }

  @override
  void dispose() {
    _descCtrl.dispose();
    _obsCtrl.dispose();
    super.dispose();
  }

  Future<void> _cargarEquipos() async {
    try {
      final data = await BibliotecaService(ApiClient()).listarEquipos();
      setState(() => _equipos = data);
    } catch (e) {
      if (mounted) showError(context, e);
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _crear() async {
    if (!_formKey.currentState!.validate()) return;
    if (_equipoSel == null) {
      showError(context, 'Seleccioná un equipo');
      return;
    }
    setState(() => _saving = true);
    try {
      await OrdenesService(ApiClient()).crear(
        equipoId: _equipoSel!.id,
        tipo: _tipo,
        descripcion: _descCtrl.text.trim(),
        observaciones: _obsCtrl.text.trim(),
      );
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      if (mounted) showError(context, e);
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Nueva orden de trabajo')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Form(
                key: _formKey,
                child: Column(
                  children: [
                    DropdownButtonFormField<EquipoCard>(
                      value: _equipoSel,
                      hint: const Text('Seleccionar equipo'),
                      items: _equipos
                          .map((e) => DropdownMenuItem(
                              value: e,
                              child: Text(e.nombre,
                                  overflow: TextOverflow.ellipsis)))
                          .toList(),
                      onChanged: (v) => setState(() => _equipoSel = v),
                      decoration: const InputDecoration(
                          labelText: 'Equipo *',
                          border: OutlineInputBorder()),
                      validator: (v) => v == null ? 'Requerido' : null,
                    ),
                    const SizedBox(height: 16),
                    DropdownButtonFormField<String>(
                      value: _tipo,
                      items: const [
                        DropdownMenuItem(
                            value: 'CORRECTIVO',
                            child: Text('Correctivo')),
                        DropdownMenuItem(
                            value: 'PREVENTIVO',
                            child: Text('Preventivo')),
                        DropdownMenuItem(
                            value: 'MEJORA', child: Text('Mejora')),
                      ],
                      onChanged: (v) => setState(() => _tipo = v!),
                      decoration: const InputDecoration(
                          labelText: 'Tipo',
                          border: OutlineInputBorder()),
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: _descCtrl,
                      decoration: const InputDecoration(
                          labelText: 'Descripción',
                          border: OutlineInputBorder()),
                      maxLines: 3,
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: _obsCtrl,
                      decoration: const InputDecoration(
                          labelText: 'Observaciones iniciales',
                          border: OutlineInputBorder()),
                      maxLines: 3,
                    ),
                    const SizedBox(height: 24),
                    SizedBox(
                      width: double.infinity,
                      height: 48,
                      child: FilledButton(
                        onPressed: _saving ? null : _crear,
                        child: _saving
                            ? const SizedBox(
                                width: 20,
                                height: 20,
                                child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    color: Colors.white))
                            : const Text('Crear orden'),
                      ),
                    ),
                  ],
                ),
              ),
            ),
    );
  }
}
