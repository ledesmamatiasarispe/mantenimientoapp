import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

const String _kBaseUrlKey = 'base_url';
const String _kTokenKey = 'auth_token';
const String _kDefaultBase = 'http://10.0.2.2:8000';

class ApiClient {
  static final ApiClient _instance = ApiClient._();
  factory ApiClient() => _instance;
  ApiClient._();

  String _baseUrl = _kDefaultBase;
  String? _token;

  Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    _baseUrl = prefs.getString(_kBaseUrlKey) ?? _kDefaultBase;
    _token = prefs.getString(_kTokenKey);
  }

  Future<void> setBaseUrl(String url) async {
    _baseUrl = url.endsWith('/') ? url.substring(0, url.length - 1) : url;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_kBaseUrlKey, _baseUrl);
  }

  String get baseUrl => _baseUrl;

  Future<void> setToken(String? token) async {
    _token = token;
    final prefs = await SharedPreferences.getInstance();
    if (token == null) {
      await prefs.remove(_kTokenKey);
    } else {
      await prefs.setString(_kTokenKey, token);
    }
  }

  String? get token => _token;

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (_token != null) 'Authorization': 'Bearer $_token',
      };

  Uri _uri(String path, [Map<String, dynamic>? params]) {
    final uri = Uri.parse('$_baseUrl$path');
    if (params == null || params.isEmpty) return uri;
    return uri.replace(
        queryParameters: params.map((k, v) => MapEntry(k, v.toString())));
  }

  Future<dynamic> get(String path, {Map<String, dynamic>? params}) async {
    final res = await http.get(_uri(path, params), headers: _headers);
    return _handle(res);
  }

  Future<dynamic> post(String path, {dynamic body}) async {
    final res = await http.post(
      _uri(path),
      headers: _headers,
      body: body != null ? jsonEncode(body) : null,
    );
    return _handle(res);
  }

  Future<dynamic> put(String path, {dynamic body}) async {
    final res = await http.put(
      _uri(path),
      headers: _headers,
      body: body != null ? jsonEncode(body) : null,
    );
    return _handle(res);
  }

  Future<dynamic> delete(String path) async {
    final res = await http.delete(_uri(path), headers: _headers);
    return _handle(res);
  }

  Future<dynamic> postMultipart(
      String path, File file, String fieldName) async {
    final request = http.MultipartRequest('POST', _uri(path));
    if (_token != null) {
      request.headers['Authorization'] = 'Bearer $_token';
    }
    request.files.add(await http.MultipartFile.fromPath(fieldName, file.path));
    final streamed = await request.send();
    final res = await http.Response.fromStream(streamed);
    return _handle(res);
  }

  Future<List<int>> getBytes(String path) async {
    final res = await http.get(_uri(path), headers: {
      if (_token != null) 'Authorization': 'Bearer $_token',
    });
    if (res.statusCode == 401) throw AuthException();
    if (res.statusCode >= 400) throw ApiException(res.statusCode, 'Error ${res.statusCode}');
    return res.bodyBytes;
  }

  dynamic _handle(http.Response res) {
    final body = utf8.decode(res.bodyBytes);
    if (res.statusCode == 401) throw AuthException();
    if (res.statusCode == 204) return null;
    if (res.statusCode >= 400) {
      String detail = '';
      try {
        detail = (jsonDecode(body) as Map)['detail']?.toString() ?? '';
      } catch (_) {}
      throw ApiException(
          res.statusCode, detail.isNotEmpty ? detail : 'Error ${res.statusCode}');
    }
    if (body.isEmpty) return null;
    return jsonDecode(body);
  }
}

class ApiException implements Exception {
  final int statusCode;
  final String message;
  ApiException(this.statusCode, this.message);
  @override
  String toString() => message;
}

class AuthException implements Exception {}
