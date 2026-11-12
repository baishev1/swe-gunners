import 'package:biletflow_staff/core/network/api_client.dart';
import 'package:biletflow_staff/core/network/mock_api_adapter.dart';
import 'package:biletflow_staff/core/network/mock_fixtures.dart';
import 'package:biletflow_staff/core/storage/token_storage.dart';
import 'package:biletflow_staff/features/auth/session_controller.dart';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'test_storage.dart';

void main() {
  late ProviderContainer container;
  late MockServer server;
  late Dio dio;
  late MemoryTokenStorage storage;
  setUp(() async {
    server = MockServer(latency: Duration.zero);
    storage = MemoryTokenStorage(demoToken);
    container = ProviderContainer(
      overrides: [
        mockServerProvider.overrideWithValue(server),
        tokenStorageProvider.overrideWithValue(storage),
      ],
    );
    await container.read(sessionProvider.future);
    dio = container.read(dioProvider);
  });
  tearDown(() => container.dispose());

  Future<Map<String, dynamic>> verify(String code) async =>
      (await dio.post<Map<String, dynamic>>(
        'checkin/verify',
        data: {'event_id': demoEventId, 'qr_code': code},
      )).data!;
  Future<Map<String, dynamic>> change(
    String ticketId, {
    bool undo = false,
  }) async => (await dio.post<Map<String, dynamic>>(
    undo ? 'checkin/undo' : 'checkin/admit',
    data: {'event_id': demoEventId, 'ticket_id': ticketId},
  )).data!;
  Matcher status(int code) => isA<DioException>().having(
    (e) => e.response?.statusCode,
    'HTTP status',
    code,
  );

  test(
    'Existing event contracts stay raw arrays with nested venue and timezone',
    () async {
      final events = (await dio.get<List<dynamic>>('checkin/events')).data!;
      expect(events, hasLength(2));
      expect(events.any((e) => e['id'] == unassignedEventId), isFalse);
      final detail = (await dio.get<Map<String, dynamic>>(
        'events/detail',
        queryParameters: {'event_id': demoEventId},
      )).data!;
      expect(detail['timezone'], 'Asia/Almaty');
      expect(detail['venue']['address'], isA<String>());
      expect(detail.containsKey('checked_in'), isFalse);
    },
  );

  test('Invalid login does not discard an existing session', () async {
    await expectLater(
      dio.post<dynamic>(
        'auth/login',
        data: {'email': demoEmail, 'password': 'wrong'},
        options: Options(extra: {'requiresAuth': false}),
      ),
      throwsA(status(401)),
    );
    expect(storage.token, demoToken);
  });

  test('Login and password reset use the same mock HTTP transport', () async {
    final response = await dio.post<Map<String, dynamic>>(
      'auth/login',
      data: {'email': demoEmail, 'password': demoPassword},
      options: Options(extra: {'requiresAuth': false}),
    );
    expect(response.data!['access_token'], demoToken);
    final reset = await dio.post<dynamic>(
      'auth/forgot-password',
      data: {'email': 'unknown@example.test'},
      options: Options(extra: {'requiresAuth': false}),
    );
    expect(reset.statusCode, 204);
  });

  test(
    'Verify does not admit; admit, duplicate rejection and undo update totals',
    () async {
      final initial = server.summary(demoEventId)['checked_in'] as int;
      final verified = await verify('DEMO-VALID');
      final ticketId = verified['ticket']['id'] as String;
      expect(verified['result'], 'valid');
      expect(server.summary(demoEventId)['checked_in'], initial);
      final admitted = await change(ticketId);
      expect(admitted['ticket']['status'], 'checked_in');
      expect(admitted['summary']['checked_in'], initial + 1);
      expect((await verify('DEMO-VALID'))['result'], 'checked_in');
      await expectLater(change(ticketId), throwsA(status(409)));
      final undone = await change(ticketId, undo: true);
      expect(undone['ticket']['status'], 'valid');
      expect(undone['summary']['checked_in'], initial);
      expect((await verify('DEMO-VALID'))['result'], 'valid');
    },
  );

  test('Concurrent admission requests allow exactly one success', () async {
    final ticketId = (await verify('DEMO-VALID'))['ticket']['id'] as String;
    final results = await Future.wait([
      for (var i = 0; i < 2; i++)
        change(
          ticketId,
        ).then<Object>((value) => value, onError: (Object error) => error),
    ]);
    expect(results.whereType<Map<String, dynamic>>(), hasLength(1));
    expect(results.whereType<DioException>().single.response?.statusCode, 409);
  });

  for (final (code, result) in [
    ('DEMO-CANCELLED', 'cancelled'),
    ('DEMO-REFUNDED', 'refunded'),
    ('DEMO-OTHER', 'wrong_event'),
    ('https://biletflow.demo/campaign/test', 'campaign_qr'),
    ('tampered', 'invalid'),
  ]) {
    test('$result never grants admission', () async {
      final response = await verify(code);
      expect(response['result'], result);
      expect(response['can_check_in'], isFalse);
      if (response['ticket'] != null) {
        await expectLater(
          change(response['ticket']['id'] as String),
          throwsA(status(409)),
        );
      }
    });
  }

  test('Manual search and details share scanner admission state', () async {
    final verified = await verify('DEMO-VALID');
    final ticketId = verified['ticket']['id'] as String;
    await change(ticketId);
    final search = await dio.get<Map<String, dynamic>>(
      'checkin/attendees',
      queryParameters: {
        'event_id': demoEventId,
        'q': 'guest1@example.test',
        'limit': 3,
        'offset': 0,
      },
    );
    expect(search.data!['total'], 1);
    expect(search.data!['items'][0]['status'], 'checked_in');
    expect(search.data!['items'][0].containsKey('qr_code'), isFalse);
    final detail = await dio.get<Map<String, dynamic>>(
      'checkin/tickets/detail',
      queryParameters: {'event_id': demoEventId, 'ticket_id': ticketId},
    );
    expect(detail.data!['status'], 'checked_in');
    expect(detail.data!['seat'], '12');
  });

  test(
    'Pagination has no duplicate records and reports complete count',
    () async {
      final first = (await dio.get<Map<String, dynamic>>(
        'checkin/attendees',
        queryParameters: {'event_id': demoEventId, 'limit': 3},
      )).data!;
      final second = (await dio.get<Map<String, dynamic>>(
        'checkin/attendees',
        queryParameters: {'event_id': demoEventId, 'limit': 3, 'offset': 3},
      )).data!;
      final all = [...first['items'] as List, ...second['items'] as List];
      expect(all.length, first['total']);
      expect(all.map((e) => e['id']).toSet().length, all.length);
    },
  );

  test(
    'Unassigned/revoked events and forbidden undo are rejected server-side',
    () async {
      await expectLater(
        dio.get<dynamic>(
          'events/detail',
          queryParameters: {'event_id': unassignedEventId},
        ),
        throwsA(status(403)),
      );
      final locked = await verify('DEMO-NO-UNDO');
      await expectLater(
        change(locked['ticket']['id'] as String, undo: true),
        throwsA(status(403)),
      );
      server.revoked = true;
      await expectLater(verify('DEMO-VALID'), throwsA(status(403)));
      expect(storage.token, demoToken);
    },
  );

  test('Cancelled event cannot verify or admit a ticket', () async {
    await expectLater(
      dio.post<dynamic>(
        'checkin/verify',
        data: {'event_id': cancelledEventId, 'qr_code': 'DEMO-VALID'},
      ),
      throwsA(status(409)),
    );
  });

  test(
    'Offline/server errors preserve session; token expiry clears it',
    () async {
      server.connection = DemoConnection.offline;
      await expectLater(verify('DEMO-VALID'), throwsA(isA<DioException>()));
      expect(storage.token, demoToken);
      server.connection = DemoConnection.serverError;
      await expectLater(verify('DEMO-VALID'), throwsA(status(503)));
      expect(storage.token, demoToken);
      server.connection = DemoConnection.normal;
      server.expired = true;
      await expectLater(verify('DEMO-VALID'), throwsA(status(401)));
      expect(storage.token, isNull);
      expect(await container.read(sessionProvider.future), isNull);
    },
  );
}
