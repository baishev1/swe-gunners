import 'package:biletflow_staff/core/storage/token_storage.dart';

class MemoryTokenStorage extends TokenStorage {
  MemoryTokenStorage([this.token, this.refreshToken]);
  String? token;
  String? refreshToken;

  @override
  Future<String?> read() async => token;

  @override
  Future<String?> readRefresh() async => refreshToken;

  @override
  Future<void> write(String token, [String? refreshToken]) async {
    this.token = token;
    if (refreshToken != null) this.refreshToken = refreshToken;
  }

  @override
  Future<void> delete() async => token = refreshToken = null;
}
