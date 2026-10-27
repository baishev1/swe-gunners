import 'package:flutter_riverpod/flutter_riverpod.dart';

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

  /// Call with the access token returned by a successful authentication request.
  Future<void> saveToken(String token) {
    if (token.trim().isEmpty) {
      throw ArgumentError('An access token must not be empty.');
    }
    return _enqueue(() async {
      await ref.read(tokenStorageProvider).write(token);
      state = AsyncData(token);
    });
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
