import '../core/api_client.dart';
import '../models/tecnico.dart';

class AuthService {
  final ApiClient _client;
  AuthService(this._client);

  Future<Map<String, dynamic>> login(String legajo, String password) async {
    final data = await _client.post('/api/auth/login', body: {
      'legajo': legajo,
      'password': password,
    });
    final tecnico =
        Tecnico.fromJson(data['tecnico'] as Map<String, dynamic>);
    return {
      'token': data['access_token'] as String,
      'tecnico': tecnico,
    };
  }

  Future<Tecnico> me() async {
    final data = await _client.get('/api/auth/me');
    return Tecnico.fromJson(data as Map<String, dynamic>);
  }
}
