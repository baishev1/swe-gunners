import 'package:biletflow_staff/core/storage/token_storage.dart';

class MemoryTokenStorage extends TokenStorage {
  MemoryTokenStorage([this.token]);
  String? token;

  @override
  Future<String?> read() async => token;

  @override
  Future<void> write(String token) async => this.token = token;

  @override
  Future<void> delete() async => token = null;
}
