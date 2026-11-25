import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_client.dart';
import '../../core/storage/token_storage.dart';

final sessionProvider = AsyncNotifierProvider<SessionController, String?>(
  SessionController.new,
  retry: (_, _) => null,
);

class SessionController extends AsyncNotifier<String?> {
  // Serialize writes/deletes so logout and a new login cannot race in storage.
  Future<void> _pending = Future.value();
  bool mustClear = false;

  @override
  Future<String?> build() => ref.read(tokenStorageProvider).read();

  /// Call with the tokens returned by a successful authentication request.
  Future<void> saveToken(String token, [String? refreshToken]) {
    if (token.trim().isEmpty) {
      throw ArgumentError('An access token must not be empty.');
    }
    return _enqueue(() async {
      await ref.read(tokenStorageProvider).write(token, refreshToken);
      state = AsyncData(token);
    });
  }

  /// Trades the stored refresh token for a new pair after [expiredToken] got a
  /// 401. Returns null and signs out when the backend rejects the refresh.
  Future<String?> refresh(String expiredToken) async {
    String? token;
    await _enqueue(() async {
      final current = state.asData?.value;
      // A parallel request already refreshed (or signed out); reuse its result.
      if (current != expiredToken) {
        token = current;
        return;
      }
      final storage = ref.read(tokenStorageProvider);
      final refreshToken = await storage.readRefresh();
      if (refreshToken == null) return _clear();
      try {
        final response = await ref
            .read(dioProvider)
            .post<Map<String, dynamic>>(
              'auth/refresh',
              data: {'refresh_token': refreshToken},
              options: Options(extra: {'requiresAuth': false}),
            );
        final fresh = response.data!['access_token'] as String;
        await storage.write(fresh, response.data!['refresh_token'] as String);
        state = AsyncData(fresh);
        token = fresh;
      } on DioException catch (error) {
        // Offline or server errors keep the session; only a rejection ends it.
        if (error.response?.statusCode != 401) rethrow;
        await _clear();
      }
    });
    return token;
  }

  Future<void> logout() => _enqueue(_clear);

  /// Ignore failures from requests sent with a previous session's token.
  Future<void> invalidate(String token) => _enqueue(() async {
    if (state.asData?.value == token) await _clear();
  });

  Future<void> _clear() async {
    try {
      await ref.read(tokenStorageProvider).delete();
      mustClear = false;
      state = const AsyncData(null);
    } catch (error, stack) {
      // Block authenticated UI/requests if secure storage could not be cleared.
      mustClear = true;
      state = AsyncError(error, stack);
      rethrow;
    }
  }

  Future<void> _enqueue(Future<void> Function() action) {
    final operation = _pending.then((_) async {
      // Wait for startup restoration before changing the session.
      if (state.isLoading) await future;
      await action();
    });
    _pending = operation.then<void>(
      (_) {},
      onError: (Object _, StackTrace _) {},
    );
    return operation;
  }
}
