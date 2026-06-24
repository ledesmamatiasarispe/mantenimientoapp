import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';
import 'package:http/http.dart' as http;
import '../../core/api_client.dart';
import '../../core/app_state.dart';
import '../../models/orden.dart';
import '../../models/repuesto.dart';
import '../../services/ordenes_service.dart';
import '../../services/biblioteca_service.dart';
import '../../widgets/estado_chip.dart';
import '../../widgets/app_error.dart';

class OrdenDetailScreen extends StatefulWidget {
  final int ordenId;
  const OrdenDetailScreen({super.key, required this.ordenId});

  @override
  State<OrdenDetailScreen> createState() => _OrdenDetailScreenState();
}

class _OrdenDetailScreenState extends State<OrdenDetailScreen> {
  late final OrdenesService _svc;
  OrdenDetail? _orden;
  bool _loading = true;
  String? _error;
  bool _changed = false;

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
      final data = await _svc.obtener(widget.ordenId);
      setState(() => _orden = data);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _run(Future<OrdenDetail> Function() action) async {
    try {
      final updated = await action();
      setState(() {
        _orden = updated;
        _changed = true;
      });
    } catch (e) {
      if (mounted) showError(context, e);
    }
  }

  Future<void> _aceptar() =>
      _run(() => _svc.aceptar(widget.ordenId));

  Future<void> _cancelarAceptacion() =>
      _run(() => _svc.cancelarAceptacion(widget.ordenId));

  Future<void> _completar() async {
    final orden = _orden!;
    if (orden.equipoHorasTrabajoActivo) {
      final result = await _pedirCompletarInfo(
          context, orden.equipoHorasTrabajoActual);
      if (!mounted || result == null) return;
      _run(() => _svc.completar(
            widget.ordenId,
            observaciones: result['observaciones'] as String,
            horasTrabajo: result['horas_trabajo'] as double,
          ));
      return;
    }
    final obs = await _pedirTexto(
        context, 'Observaciones finales (opcional)');
    if (!mounted) return;
    _run(() => _svc.completar(widget.ordenId, observaciones: obs ?? ''));
  }

  Future<void> _agregarObservacion() async {
    final texto = await _pedirTexto(context, 'Nueva observación');
    if (texto == null || texto.trim().isEmpty) return;
    if (!mounted) return;
    _run(() => _svc.agregarObservacion(widget.ordenId, texto.trim()));
  }

  Future<void> _subirFoto() async {
    final picker = ImagePicker();
    final picked = await picker.pickImage(source: ImageSource.camera);
    if (picked == null) return;
    if (!mounted) return;
    _run(() => _svc.subirFoto(widget.ordenId, File(picked.path)));
  }

  Future<void> _subirFotoGaleria() async {
    final picker = ImagePicker();
    final picked = await picker.pickImage(source: ImageSource.gallery);
    if (picked == null) return;
    if (!mounted) return;
    _run(() => _svc.subirFoto(widget.ordenId, File(picked.path)));
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: true,
      onPopInvokedWithResult: (didPop, _) {
        if (didPop && _changed) {
          Navigator.of(context).pop(true);
        }
      },
      child: Scaffold(
        appBar: AppBar(
          title: Text('Orden #${widget.ordenId}'),
          leading: IconButton(
            icon: const Icon(Icons.arrow_back),
            onPressed: () => Navigator.pop(context, _changed),
          ),
          actions: [
            IconButton(icon: const Icon(Icons.refresh), onPressed: _cargar),
          ],
        ),
        body: _loading
            ? const Center(child: CircularProgressIndicator())
            : _error != null
                ? AppError(message: _error!, onRetry: _cargar)
                : _buildBody(),
      ),
    );
  }

  Widget _buildBody() {
    final orden = _orden!;
    final state = context.read<AppState>();
    final tecnicoId = state.tecnico?.id;
    final isAdmin = state.tecnico?.esAdmin ?? false;
    final cerrada =
        orden.estado == 'COMPLETADA' || orden.estado == 'CANCELADA';
    final soyColaborador =
        orden.colaboradores.any((c) => c.id == tecnicoId);
    final soyPrincipal = orden.tecnicoId == tecnicoId;

    return RefreshIndicator(
      onRefresh: _cargar,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // ── Header ────────────────────────────────────────────────────
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(orden.equipoNombre,
                            style: Theme.of(context).textTheme.titleLarge),
                      ),
                      EstadoChip(orden.estado),
                    ],
                  ),
                  const SizedBox(height: 4),
                  TipoChip(orden.tipo),
                  if (orden.descripcion.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Text(orden.descripcion),
                  ],
                  const SizedBox(height: 8),
                  _InfoRow('Equipo', '${orden.equipoMarca} ${orden.equipoModelo}'.trim()),
                  _InfoRow('Ubicación', orden.equipoUbicacion),
                  _InfoRow('Apertura', orden.fechaApertura),
                  if (orden.fechaCierre.isNotEmpty)
                    _InfoRow('Cierre', orden.fechaCierre),
                  if (orden.tecnicoNombre.isNotEmpty)
                    _InfoRow('Técnico', orden.tecnicoNombre),
                ],
              ),
            ),
          ),

          // ── Acciones ──────────────────────────────────────────────────
          if (!cerrada) ...[
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                if (orden.estado == 'PENDIENTE' ||
                    (orden.estado == 'EN_PROGRESO' && !soyColaborador))
                  FilledButton.icon(
                    onPressed: _aceptar,
                    icon: const Icon(Icons.check),
                    label: const Text('Aceptar'),
                  ),
                if (soyColaborador)
                  OutlinedButton.icon(
                    onPressed: _cancelarAceptacion,
                    icon: const Icon(Icons.undo),
                    label: const Text('Cancelar aceptación'),
                  ),
                if (orden.estado == 'EN_PROGRESO' &&
                    (soyPrincipal || isAdmin))
                  FilledButton.icon(
                    onPressed: _completar,
                    icon: const Icon(Icons.done_all),
                    label: const Text('Completar'),
                    style: FilledButton.styleFrom(
                        backgroundColor: const Color(0xFF0E6B52)),
                  ),
                OutlinedButton.icon(
                  onPressed: _agregarObservacion,
                  icon: const Icon(Icons.comment),
                  label: const Text('Observación'),
                ),
                OutlinedButton.icon(
                  onPressed: _subirFoto,
                  icon: const Icon(Icons.camera_alt),
                  label: const Text('Foto'),
                ),
                OutlinedButton.icon(
                  onPressed: _subirFotoGaleria,
                  icon: const Icon(Icons.photo_library),
                  label: const Text('Galería'),
                ),
              ],
            ),
          ],

          // ── Colaboradores ─────────────────────────────────────────────
          if (orden.colaboradores.isNotEmpty) ...[
            const SizedBox(height: 16),
            _SectionTitle('Colaboradores'),
            Wrap(
              spacing: 8,
              children: orden.colaboradores
                  .map((c) => Chip(label: Text(c.nombreCompleto)))
                  .toList(),
            ),
          ],

          // ── Observaciones ─────────────────────────────────────────────
          if (orden.observaciones.isNotEmpty) ...[
            const SizedBox(height: 16),
            _SectionTitle('Observaciones'),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Text(orden.observaciones),
              ),
            ),
          ],

          // ── Repuestos ─────────────────────────────────────────────────
          const SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _SectionTitle('Repuestos (${orden.repuestos.length})'),
              if (!cerrada)
                TextButton.icon(
                  onPressed: () => _agregarRepuesto(orden),
                  icon: const Icon(Icons.add),
                  label: const Text('Agregar'),
                ),
            ],
          ),
          if (orden.repuestos.isEmpty)
            const Text('Sin repuestos cargados',
                style: TextStyle(color: Colors.grey))
          else
            ...orden.repuestos.map((r) => _RepuestoTile(
                  r,
                  cerrada
                      ? null
                      : () => _run(() =>
                          _svc.quitarRepuesto(widget.ordenId, r.id)),
                )),

          // ── Programas / Pasos ─────────────────────────────────────────
          if (orden.programas.isNotEmpty) ...[
            const SizedBox(height: 16),
            _SectionTitle(
                'Programas de mantenimiento (${orden.programas.length})'),
            ...orden.programas.map((p) => _ProgramaTile(
                  p,
                  cerrada ? null : (pasoId) => _run(() =>
                      _svc.togglePaso(widget.ordenId, pasoId)),
                )),
          ],

          // ── Fotos ─────────────────────────────────────────────────────
          if (orden.fotos.isNotEmpty) ...[
            const SizedBox(height: 16),
            _SectionTitle('Fotos (${orden.fotos.length})'),
            SizedBox(
              height: 120,
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                itemCount: orden.fotos.length,
                separatorBuilder: (_, __) => const SizedBox(width: 8),
                itemBuilder: (_, i) => _FotoItem(
                  ordenId: widget.ordenId,
                  foto: orden.fotos[i],
                  onDelete: cerrada
                      ? null
                      : () => _run(() =>
                          _svc.eliminarFoto(
                              widget.ordenId, orden.fotos[i].id)),
                ),
              ),
            ),
          ],

          const SizedBox(height: 80),
        ],
      ),
    );
  }

  Future<void> _agregarRepuesto(OrdenDetail orden) async {
    final result = await showModalBottomSheet<Map<String, dynamic>>(
      context: context,
      isScrollControlled: true,
      builder: (_) => _AgregarRepuestoSheet(),
    );
    if (result == null) return;
    _run(() => _svc.agregarRepuesto(
          widget.ordenId,
          result['repuesto_id'] as int,
          result['cantidad'] as double,
        ));
  }
}

class _InfoRow extends StatelessWidget {
  final String label;
  final String value;
  const _InfoRow(this.label, this.value);

  @override
  Widget build(BuildContext context) {
    if (value.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 90,
            child: Text('$label:',
                style: TextStyle(
                    color: Theme.of(context)
                        .colorScheme
                        .onSurface
                        .withOpacity(0.6),
                    fontSize: 13)),
          ),
          Expanded(child: Text(value, style: const TextStyle(fontSize: 13))),
        ],
      ),
    );
  }
}

class _SectionTitle extends StatelessWidget {
  final String text;
  const _SectionTitle(this.text);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Text(text,
          style: Theme.of(context)
              .textTheme
              .titleMedium
              ?.copyWith(fontWeight: FontWeight.w700)),
    );
  }
}

class _RepuestoTile extends StatelessWidget {
  final RepuestoOrdenItem repuesto;
  final VoidCallback? onDelete;
  const _RepuestoTile(this.repuesto, this.onDelete);

  @override
  Widget build(BuildContext context) {
    return ListTile(
      dense: true,
      title: Text(repuesto.descripcion),
      subtitle: Text('Cantidad: ${repuesto.cantidad}'),
      trailing: onDelete != null
          ? IconButton(
              icon: const Icon(Icons.delete_outline, size: 20),
              onPressed: onDelete)
          : null,
    );
  }
}

class _ProgramaTile extends StatelessWidget {
  final ProgramaResumen programa;
  final void Function(int pasoId)? onToggle;
  const _ProgramaTile(this.programa, this.onToggle);

  @override
  Widget build(BuildContext context) {
    final completados = programa.pasos.where((p) => p.completado).length;
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ExpansionTile(
        title: Text(programa.descripcion),
        subtitle: Text(
            '${programa.frecuenciaMeses} meses • $completados/${programa.pasos.length} pasos'),
        children: programa.pasos
            .map((p) => CheckboxListTile(
                  value: p.completado,
                  onChanged: onToggle != null
                      ? (_) => onToggle!(p.id)
                      : null,
                  title: Text(p.descripcion),
                  subtitle: p.observaciones.isNotEmpty
                      ? Text(p.observaciones,
                          style: const TextStyle(fontSize: 12))
                      : null,
                  dense: true,
                ))
            .toList(),
      ),
    );
  }
}

class _FotoItem extends StatefulWidget {
  final int ordenId;
  final FotoOrdenItem foto;
  final VoidCallback? onDelete;
  const _FotoItem(
      {required this.ordenId, required this.foto, this.onDelete});

  @override
  State<_FotoItem> createState() => _FotoItemState();
}

class _FotoItemState extends State<_FotoItem> {
  Uint8List? _bytes;

  @override
  void initState() {
    super.initState();
    _fetchImage();
  }

  Future<void> _fetchImage() async {
    try {
      final bytes = await ApiClient().getBytes(
          '/api/ordenes/${widget.ordenId}/fotos/${widget.foto.id}');
      if (mounted) setState(() => _bytes = Uint8List.fromList(bytes));
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        Container(
          width: 120,
          height: 120,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(8),
            color: Colors.grey.shade200,
          ),
          child: _bytes != null
              ? ClipRRect(
                  borderRadius: BorderRadius.circular(8),
                  child: Image.memory(_bytes!, fit: BoxFit.cover),
                )
              : const Center(child: CircularProgressIndicator()),
        ),
        if (widget.onDelete != null)
          Positioned(
            top: 4,
            right: 4,
            child: InkWell(
              onTap: widget.onDelete,
              child: Container(
                padding: const EdgeInsets.all(2),
                decoration: BoxDecoration(
                  color: Colors.black54,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(Icons.close, size: 16, color: Colors.white),
              ),
            ),
          ),
      ],
    );
  }
}

class _AgregarRepuestoSheet extends StatefulWidget {
  @override
  State<_AgregarRepuestoSheet> createState() => _AgregarRepuestoSheetState();
}

class _AgregarRepuestoSheetState extends State<_AgregarRepuestoSheet> {
  List<RepuestoDisponible> _repuestos = [];
  RepuestoDisponible? _selected;
  final _cantCtrl = TextEditingController(text: '1');
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    BibliotecaService(ApiClient()).listarRepuestos().then((list) {
      if (mounted) setState(() {
        _repuestos = list;
        _loading = false;
      });
    });
  }

  @override
  void dispose() {
    _cantCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
          bottom: MediaQuery.of(context).viewInsets.bottom + 16,
          left: 16,
          right: 16,
          top: 16),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Agregar repuesto',
              style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 16),
          if (_loading)
            const Center(child: CircularProgressIndicator())
          else
            DropdownButtonFormField<RepuestoDisponible>(
              value: _selected,
              hint: const Text('Seleccionar repuesto'),
              items: _repuestos
                  .map((r) => DropdownMenuItem(
                      value: r,
                      child: Text('${r.nombre} (stock: ${r.stockActual})')))
                  .toList(),
              onChanged: (v) => setState(() => _selected = v),
              decoration: const InputDecoration(border: OutlineInputBorder()),
            ),
          const SizedBox(height: 12),
          TextFormField(
            controller: _cantCtrl,
            decoration: const InputDecoration(
              labelText: 'Cantidad',
              border: OutlineInputBorder(),
            ),
            keyboardType:
                const TextInputType.numberWithOptions(decimal: true),
          ),
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: FilledButton(
              onPressed: _selected == null
                  ? null
                  : () {
                      final cant =
                          double.tryParse(_cantCtrl.text) ?? 1.0;
                      Navigator.pop(context, {
                        'repuesto_id': _selected!.id,
                        'cantidad': cant,
                      });
                    },
              child: const Text('Agregar'),
            ),
          ),
        ],
      ),
    );
  }
}

Future<Map<String, dynamic>?> _pedirCompletarInfo(
    BuildContext context, double horasActuales) {
  return showDialog<Map<String, dynamic>>(
    context: context,
    builder: (_) => _CompletarOrdenDialog(horasActuales: horasActuales),
  );
}

class _CompletarOrdenDialog extends StatefulWidget {
  final double horasActuales;
  const _CompletarOrdenDialog({required this.horasActuales});

  @override
  State<_CompletarOrdenDialog> createState() => _CompletarOrdenDialogState();
}

class _CompletarOrdenDialogState extends State<_CompletarOrdenDialog> {
  late final TextEditingController _obsCtrl;
  late final TextEditingController _horasCtrl;

  @override
  void initState() {
    super.initState();
    _obsCtrl = TextEditingController();
    _horasCtrl =
        TextEditingController(text: widget.horasActuales.toString());
  }

  @override
  void dispose() {
    _obsCtrl.dispose();
    _horasCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final horas = double.tryParse(_horasCtrl.text);
    final valido = horas != null && horas > widget.horasActuales;
    return AlertDialog(
      title: const Text('Completar orden'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            TextField(
              controller: _horasCtrl,
              autofocus: true,
              keyboardType:
                  const TextInputType.numberWithOptions(decimal: true),
              decoration: InputDecoration(
                labelText: 'Horas de trabajo actuales',
                helperText:
                    'Actual: ${widget.horasActuales}. Debe ser mayor.',
                border: const OutlineInputBorder(),
                errorText: _horasCtrl.text.isNotEmpty && !valido
                    ? 'Debe ser mayor a ${widget.horasActuales}'
                    : null,
              ),
              onChanged: (_) => setState(() {}),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _obsCtrl,
              maxLines: 4,
              decoration: const InputDecoration(
                labelText: 'Observaciones finales (opcional)',
                border: OutlineInputBorder(),
              ),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancelar')),
        FilledButton(
          onPressed: !valido
              ? null
              : () => Navigator.pop(context, {
                    'observaciones': _obsCtrl.text,
                    'horas_trabajo': horas,
                  }),
          child: const Text('Aceptar'),
        ),
      ],
    );
  }
}

Future<String?> _pedirTexto(
    BuildContext context, String titulo) async {
  final ctrl = TextEditingController();
  return showDialog<String>(
    context: context,
    builder: (_) => AlertDialog(
      title: Text(titulo),
      content: TextField(
        controller: ctrl,
        maxLines: 4,
        autofocus: true,
        decoration: const InputDecoration(border: OutlineInputBorder()),
      ),
      actions: [
        TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancelar')),
        FilledButton(
            onPressed: () => Navigator.pop(context, ctrl.text),
            child: const Text('Aceptar')),
      ],
    ),
  );
}
