import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

final tokenStorageProvider = Provider((ref) => TokenStorage());

class TokenStorage {
  static const _key = 'access_token';
  static const _refreshKey = 'refresh_token';
  final _storage = const FlutterSecureStorage();

  Future<String?> read() => _storage.read(key: _key);
  Future<String?> readRefresh() => _storage.read(key: _refreshKey);

  Future<void> write(String token, [String? refreshToken]) async {
    await _storage.write(key: _key, value: token);
    if (refreshToken != null) {
      await _storage.write(key: _refreshKey, value: refreshToken);
    }
  }

  Future<void> delete() async {
    await _storage.delete(key: _key);
    await _storage.delete(key: _refreshKey);
  }
}
