import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/api_client.dart';
import '../core/app_state.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _legajoCtrl = TextEditingController();
  final _passCtrl = TextEditingController();
  final _urlCtrl = TextEditingController();
  bool _loading = false;
  bool _showUrl = false;

  @override
  void initState() {
    super.initState();
    _urlCtrl.text = ApiClient().baseUrl;
  }

  @override
  void dispose() {
    _legajoCtrl.dispose();
    _passCtrl.dispose();
    _urlCtrl.dispose();
    super.dispose();
  }

  Future<void> _login() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _loading = true);
    try {
      if (_showUrl) {
        await ApiClient().setBaseUrl(_urlCtrl.text.trim());
      }
      await context.read<AppState>().login(
            _legajoCtrl.text.trim(),
            _passCtrl.text,
          );
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(e.toString()),
            backgroundColor: Theme.of(context).colorScheme.error,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(32),
            child: Form(
              key: _formKey,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.engineering,
                      size: 72, color: Color(0xFF0E6B52)),
                  const SizedBox(height: 8),
                  Text('Gestión Mantenimiento',
                      style: Theme.of(context).textTheme.headlineSmall),
                  const SizedBox(height: 32),
                  TextFormField(
                    controller: _legajoCtrl,
                    decoration: const InputDecoration(
                      labelText: 'Legajo',
                      prefixIcon: Icon(Icons.badge),
                      border: OutlineInputBorder(),
                    ),
                    textInputAction: TextInputAction.next,
                    validator: (v) =>
                        (v == null || v.trim().isEmpty) ? 'Requerido' : null,
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    controller: _passCtrl,
                    decoration: const InputDecoration(
                      labelText: 'Contraseña',
                      prefixIcon: Icon(Icons.lock),
                      border: OutlineInputBorder(),
                    ),
                    obscureText: true,
                    textInputAction: TextInputAction.done,
                    onFieldSubmitted: (_) => _login(),
                    validator: (v) =>
                        (v == null || v.isEmpty) ? 'Requerido' : null,
                  ),
                  const SizedBox(height: 8),
                  TextButton.icon(
                    onPressed: () => setState(() => _showUrl = !_showUrl),
                    icon: Icon(_showUrl
                        ? Icons.expand_less
                        : Icons.settings_ethernet),
                    label:
                        Text(_showUrl ? 'Ocultar servidor' : 'Configurar servidor'),
                  ),
                  if (_showUrl) ...[
                    TextFormField(
                      controller: _urlCtrl,
                      decoration: const InputDecoration(
                        labelText: 'URL del servidor',
                        hintText: 'http://192.168.1.100:8000',
                        prefixIcon: Icon(Icons.dns),
                        border: OutlineInputBorder(),
                      ),
                      keyboardType: TextInputType.url,
                    ),
                    const SizedBox(height: 8),
                  ],
                  const SizedBox(height: 16),
                  SizedBox(
                    width: double.infinity,
                    height: 48,
                    child: FilledButton(
                      onPressed: _loading ? null : _login,
                      child: _loading
                          ? const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(
                                  strokeWidth: 2, color: Colors.white),
                            )
                          : const Text('Ingresar'),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
