import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:biletflow_staff/core/network/api_client.dart';
import 'package:biletflow_staff/core/storage/token_storage.dart';
import 'package:biletflow_staff/features/auth/session_controller.dart';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'test_storage.dart';

class TestAdapter implements HttpClientAdapter {
  TestAdapter(this.respond);
  final Future<ResponseBody> Function(RequestOptions) respond;

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) => respond(options);

  @override
  void close({bool force = false}) {}
}

void main() {
  late MemoryTokenStorage storage;
  late ProviderContainer container;
  late Dio dio;

  setUp(() async {
    storage = MemoryTokenStorage('saved-token');
    container = ProviderContainer(
      overrides: [tokenStorageProvider.overrideWithValue(storage)],
    );
    await container.read(sessionProvider.future);
    dio = container.read(dioProvider);
  });
  tearDown(() => container.dispose());

  test('Saved token survives a new app container', () async {
    await container.read(sessionProvider.notifier).saveToken('new-token');
    final restarted = ProviderContainer(
      overrides: [tokenStorageProvider.overrideWithValue(storage)],
    );
    addTearDown(restarted.dispose);
    expect(await restarted.read(sessionProvider.future), 'new-token');
  });

  test('Authenticated 401 clears memory and secure storage', () async {
    dio.httpClientAdapter = TestAdapter((request) async {
      expect(request.headers['Authorization'], 'Bearer saved-token');
      return ResponseBody.fromString('', 401);
    });
    await expectLater(dio.get('events'), throwsA(isA<DioException>()));
    expect(await container.read(sessionProvider.future), isNull);
    expect(storage.token, isNull);
  });

  test('Expired access token is refreshed and the request retried', () async {
    storage.refreshToken = 'saved-refresh';
    dio.httpClientAdapter = TestAdapter((request) async {
      if (request.path == 'auth/refresh') {
        expect(request.data, {'refresh_token': 'saved-refresh'});
        expect(request.headers['Authorization'], isNull);
        return ResponseBody.fromString(
          jsonEncode({
            'access_token': 'new-token',
            'refresh_token': 'new-refresh',
            'token_type': 'bearer',
          }),
          200,
          headers: {
            Headers.contentTypeHeader: [Headers.jsonContentType],
          },
        );
      }
      if (request.headers['Authorization'] == 'Bearer new-token') {
        return ResponseBody.fromString(
          '[]',
          200,
          headers: {
            Headers.contentTypeHeader: [Headers.jsonContentType],
          },
        );
      }
      return ResponseBody.fromString('', 401);
    });

    final response = await dio.get<List<dynamic>>('events');

    expect(response.data, isEmpty);
    expect(await container.read(sessionProvider.future), 'new-token');
    expect(storage.token, 'new-token');
    expect(storage.refreshToken, 'new-refresh');
  });

  test('Rejected refresh token signs out', () async {
    storage.refreshToken = 'saved-refresh';
    final paths = <String>[];
    dio.httpClientAdapter = TestAdapter((request) async {
      paths.add(request.path);
      return ResponseBody.fromString('', 401);
    });

    await expectLater(dio.get('events'), throwsA(isA<DioException>()));

    expect(paths, ['events', 'auth/refresh']);
    expect(await container.read(sessionProvider.future), isNull);
    expect(storage.token, isNull);
    expect(storage.refreshToken, isNull);
  });

  test('Offline refresh keeps the session', () async {
    storage.refreshToken = 'saved-refresh';
    dio.httpClientAdapter = TestAdapter((request) async {
      if (request.path == 'auth/refresh') {
        throw DioException.connectionError(
          requestOptions: request,
          reason: 'offline',
        );
      }
      return ResponseBody.fromString('', 401);
    });

    await expectLater(dio.get('events'), throwsA(isA<DioException>()));

    expect(await container.read(sessionProvider.future), 'saved-token');
    expect(storage.refreshToken, 'saved-refresh');
  });

  for (final status in [403, 500]) {
    test('$status preserves session', () async {
      dio.httpClientAdapter = TestAdapter(
        (_) async => ResponseBody.fromString('', status),
      );
      await expectLater(dio.get('events'), throwsA(isA<DioException>()));
      expect(storage.token, 'saved-token');
      expect(await container.read(sessionProvider.future), 'saved-token');
    });
  }

  test('Connection failure preserves session', () async {
    dio.httpClientAdapter = TestAdapter((request) async {
      throw DioException.connectionError(
        requestOptions: request,
        reason: 'offline',
      );
    });
    await expectLater(dio.get('events'), throwsA(isA<DioException>()));
    expect(storage.token, 'saved-token');
  });

  test('Delayed 401 cannot invalidate a newer login', () async {
    final started = Completer<void>();
    final response = Completer<ResponseBody>();
    dio.httpClientAdapter = TestAdapter((request) {
      if (started.isCompleted) {
        // The stale 401 is retried with the newer login's token.
        expect(request.headers['Authorization'], 'Bearer new-token');
        return Future.value(ResponseBody.fromString('', 200));
      }
      started.complete();
      return response.future;
    });
    final request = dio.get('events');
    await started.future;
    await container.read(sessionProvider.notifier).saveToken('new-token');
    response.complete(ResponseBody.fromString('', 401));
    expect((await request).statusCode, 200);
    expect(storage.token, 'new-token');
    expect(await container.read(sessionProvider.future), 'new-token');
  });

  test('Public request 401 leaves existing session alone', () async {
    dio.httpClientAdapter = TestAdapter((request) async {
      expect(request.headers.containsKey('Authorization'), isFalse);
      return ResponseBody.fromString('', 401);
    });
    await expectLater(
      dio.post('login', options: Options(extra: {'requiresAuth': false})),
      throwsA(isA<DioException>()),
    );
    expect(storage.token, 'saved-token');
  });

  test('Token is not sent outside the configured API', () async {
    dio.httpClientAdapter = TestAdapter((request) async {
      expect(request.headers.containsKey('Authorization'), isFalse);
      return ResponseBody.fromString('', 200);
    });
    await dio.get('https://example.com/file');
    await dio.get('http://localhost:8000/other');
  });

  test('Login followed immediately by logout leaves no stored token', () async {
    final session = container.read(sessionProvider.notifier);
    await Future.wait([session.saveToken('new-token'), session.logout()]);
    expect(storage.token, isNull);
    expect(await container.read(sessionProvider.future), isNull);
  });
}
