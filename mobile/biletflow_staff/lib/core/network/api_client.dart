import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../features/auth/session_controller.dart';
import 'mock_api_adapter.dart';

final dioProvider = Provider<Dio>((ref) {
  final dio = Dio(
    BaseOptions(
      baseUrl: const String.fromEnvironment(
        'API_BASE_URL',
        defaultValue: 'http://localhost:8000/api/v1/',
      ),
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 30),
      headers: {'Accept': 'application/json'},
    ),
  );
  if (useMockApi) {
    dio.httpClientAdapter = MockApiAdapter(ref.read(mockServerProvider));
  }
  final api = Uri.parse(dio.options.baseUrl);
  dio.interceptors.add(
    InterceptorsWrapper(
      onRequest: (options, handler) async {
        // Public calls (including login) must opt out of session handling.
        final uri = options.uri;
        final trusted =
            uri.origin == api.origin &&
            (uri.path == api.path ||
                uri.path.startsWith(
                  api.path.endsWith('/') ? api.path : '${api.path}/',
                ));
        if (options.extra['requiresAuth'] == false || !trusted) {
          handler.next(options);
          return;
        }
        try {
          final token = await ref.read(sessionProvider.future);
          if (token != null) options.headers['Authorization'] = 'Bearer $token';
          handler.next(options);
        } catch (error, stack) {
          handler.reject(
            DioException(
              requestOptions: options,
              error: error,
              stackTrace: stack,
            ),
          );
        }
      },
      onError: (error, handler) async {
        final authorization = error.requestOptions.headers['Authorization'];
        if (error.response?.statusCode == 401 &&
            error.requestOptions.extra['requiresAuth'] != false &&
            authorization is String &&
            authorization.startsWith('Bearer ')) {
          try {
            await ref
                .read(sessionProvider.notifier)
                .invalidate(authorization.substring(7));
          } catch (_) {
            // The session exposes storage failures; preserve the HTTP error.
          }
        }
        handler.next(error);
      },
    ),
  );
  ref.onDispose(() => dio.close(force: true));
  return dio;
});
