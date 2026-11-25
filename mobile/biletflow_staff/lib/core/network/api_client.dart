import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../features/auth/session_controller.dart';
import 'mock_api_adapter.dart';

const defaultApiBaseUrl = 'http://localhost:8000/api/v1/';

/// Overrides the HTTP transport in tests while keeping the session
/// interceptor and base configuration.
final httpClientAdapterProvider = Provider<HttpClientAdapter?>((ref) => null);

String resolveApiBaseUrl({required String configured, required bool release}) {
  final uri = Uri.tryParse(configured);
  if (uri == null || !uri.hasScheme || uri.host.isEmpty) {
    throw StateError('API_BASE_URL must be an absolute URL.');
  }
  if (release && uri.scheme != 'https') {
    throw StateError('API_BASE_URL must use HTTPS in release builds.');
  }
  return configured.endsWith('/') ? configured : '$configured/';
}

final dioProvider = Provider<Dio>((ref) {
  final dio = Dio(
    BaseOptions(
      baseUrl: resolveApiBaseUrl(
        configured: const String.fromEnvironment(
          'API_BASE_URL',
          defaultValue: defaultApiBaseUrl,
        ),
        release: kReleaseMode,
      ),
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 30),
      headers: {'Accept': 'application/json'},
    ),
  );
  final adapter = ref.watch(httpClientAdapterProvider);
  if (adapter != null) {
    dio.httpClientAdapter = adapter;
  } else if (ref.watch(useMockApiProvider)) {
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
        final options = error.requestOptions;
        final authorization = options.headers['Authorization'];
        if (error.response?.statusCode == 401 &&
            options.extra['requiresAuth'] != false &&
            authorization is String &&
            authorization.startsWith('Bearer ')) {
          final session = ref.read(sessionProvider.notifier);
          final expired = authorization.substring(7);
          if (options.extra['retried'] == true) {
            try {
              await session.invalidate(expired);
            } catch (_) {
              // The session exposes storage failures; preserve the HTTP error.
            }
          } else {
            String? token;
            try {
              token = await session.refresh(expired);
            } catch (_) {
              // Offline or storage failure; report the original 401.
            }
            if (token != null) {
              options.extra['retried'] = true;
              try {
                handler.resolve(await dio.fetch<dynamic>(options));
              } on DioException catch (retryError) {
                handler.next(retryError);
              }
              return;
            }
          }
        }
        handler.next(error);
      },
    ),
  );
  ref.onDispose(() => dio.close(force: true));
  return dio;
});
