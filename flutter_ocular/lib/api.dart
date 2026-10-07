import 'dart:convert';
import 'dart:ui' show VoidCallback;

import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

// Android emulator -> host machine. Physical phone: use your PC's LAN IP, e.g. http://192.168.1.20:8000
const baseUrl = 'http://10.0.2.2:8000';

class ApiException implements Exception {
  final String message;
  ApiException(this.message);
  @override
  String toString() => message;
}

class Api {
  static String? token;
  static VoidCallback?
  onUnauthorized; // set in main.dart -> sends user to Login

  static Future<void> loadToken() async =>
      token = (await SharedPreferences.getInstance()).getString('token');

  static Future<void> logout() async {
    token = null;
    await (await SharedPreferences.getInstance()).remove('token');
  }

  static Future<String?> savedSlug() async =>
      (await SharedPreferences.getInstance()).getString('org_slug');

  static Map<String, String> get _auth => {'Authorization': 'Bearer $token'};
  static Uri _u(String p) => Uri.parse('$baseUrl$p');

  static dynamic _handle(http.Response r) {
    final body = r.body.isEmpty ? null : jsonDecode(r.body);
    if (r.statusCode >= 200 && r.statusCode < 300) return body;
    if (r.statusCode == 401) {
      logout();
      onUnauthorized?.call();
    }
    final d = body is Map ? body['detail'] : null;
    throw ApiException(
      d is String
          ? d
          : d is List
          ? d.map((e) => e['msg']).join('\n')
          : 'Error ${r.statusCode}',
    );
  }

  // POST /signup  (creates org + first moderator)
  static Future<void> signup(Map<String, String> data) async {
    _handle(
      await http.post(
        _u('/signup'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(data),
      ),
    );
    await (await SharedPreferences.getInstance()).setString(
      'org_slug',
      data['organization_slug']!,
    );
  }

  // POST /auth/login  (OAuth2 form: field is "username" but holds the email)
  static Future<void> login(String email, String password) async {
    final r = _handle(
      await http.post(
        _u('/auth/login'),
        body: {'username': email, 'password': password},
      ),
    ); // Map body => form-encoded
    token = r['access_token'];
    await (await SharedPreferences.getInstance()).setString('token', token!);
  }

  // POST /organizations/{slug}/moderators
  static Future<void> addModerator(
    String slug,
    Map<String, String> data,
  ) async => _handle(
    await http.post(
      _u('/organizations/$slug/moderators'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(data),
    ),
  );

  // POST /organizations/persons -> person_id
  static Future<String> createPerson(
    String externalId,
    String first,
    String last,
  ) async {
    final r = _handle(
      await http.post(
        _u('/organizations/persons'),
        headers: {..._auth, 'Content-Type': 'application/json'},
        body: jsonEncode({
          'external_id': externalId,
          'first_name': first,
          'last_name': last,
        }),
      ),
    );
    return r['person_id'];
  }

  static Future<http.Response> _upload(String path, String filePath) async {
    final req = http.MultipartRequest('POST', _u(path))
      ..headers.addAll(_auth)
      ..files.add(await http.MultipartFile.fromPath('file', filePath));
    return http.Response.fromStream(await req.send());
  }

  // POST /persons/{id}/enroll -> task_id
  static Future<String> enroll(String personId, String filePath) async =>
      _handle(await _upload('/persons/$personId/enroll', filePath))['task_id'];

  // POST /recognize -> task_id
  static Future<String> recognize(String filePath) async =>
      _handle(await _upload('/recognize', filePath))['task_id'];

  // GET /export_attendance -> task_id
  static Future<String> exportAttendance() async => _handle(
    await http.get(_u('/export_attendance'), headers: _auth),
  )['task_id'];

  // GET /tasks/{id}, polled until SUCCESS (backend returns 500 on FAILURE -> ApiException)
  static Future<Map> pollTask(String id) async {
    for (var i = 0; i < 60; i++) {
      final r = _handle(await http.get(_u('/tasks/$id'), headers: _auth));
      if (r['status'] == 'SUCCESS') return Map.from(r['result'] ?? {});
      await Future.delayed(const Duration(seconds: 1));
    }
    throw ApiException('Timed out waiting for the result');
  }
}
