import 'package:flutter/material.dart';
import 'api_client.dart';
import '../models/tecnico.dart';
import '../services/auth_service.dart';

class AppState extends ChangeNotifier {
  final ApiClient client;
  Tecnico? _tecnico;

  AppState(this.client) {
    _tryRestoreSession();
  }

  Tecnico? get tecnico => _tecnico;
  bool get isLoggedIn => _tecnico != null;

  Future<void> _tryRestoreSession() async {
    if (client.token == null) return;
    try {
      final t = await AuthService(client).me();
      _tecnico = t;
      notifyListeners();
    } catch (_) {
      await client.setToken(null);
    }
  }

  Future<void> login(String legajo, String password) async {
    final result = await AuthService(client).login(legajo, password);
    await client.setToken(result['token'] as String);
    _tecnico = result['tecnico'] as Tecnico;
    notifyListeners();
  }

  Future<void> logout() async {
    await client.setToken(null);
    _tecnico = null;
    notifyListeners();
  }
}
