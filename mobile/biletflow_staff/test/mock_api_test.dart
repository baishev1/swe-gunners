import 'package:biletflow_staff/core/network/api_client.dart';
import 'package:biletflow_staff/core/network/mock_api_adapter.dart';
import 'package:biletflow_staff/core/network/mock_fixtures.dart';
import 'package:biletflow_staff/core/storage/token_storage.dart';
import 'package:biletflow_staff/features/auth/session_controller.dart';
import 'package:biletflow_staff/features/check_in/check_in_controller.dart';
import 'package:biletflow_staff/features/check_in/ticket.dart';
import 'package:biletflow_staff/features/events/event.dart';
import 'package:biletflow_staff/features/events/event_providers.dart';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'test_storage.dart';

const _ticketResponseKeys = {
  'id',
  'order_id',
  'order_item_id',
  'event_id',
  'ticket_type_id',
  'ticket_type_name',
  'attendee_name',
  'attendee_email',
  'qr_token',
  'status',
  'checked_in_at',
  'section',
  'row',
  'seat',
  'created_at',
  'updated_at',
};

const _attendeeResponseKeys = {
  'ticket_id',
  'order_id',
  'attendee_name',
  'attendee_email',
  'ticket_type_id',
  'ticket_type_name',
  'ticket_status',
  'order_status',
  'checked_in_at',
  'section',
  'row',
  'seat',
  'created_at',
};

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
        useMockApiProvider.overrideWithValue(true),
        mockServerProvider.overrideWithValue(server),
        tokenStorageProvider.overrideWithValue(storage),
      ],
    );
    await container.read(sessionProvider.future);
    dio = container.read(dioProvider);
  });
  tearDown(() => container.dispose());

  Future<Map<String, dynamic>> verify(
    String code, {
    String eventId = demoEventId,
  }) async => (await dio.get<Map<String, dynamic>>(
    'tickets/verify',
    queryParameters: {'event_id': eventId, 'qr_token': code},
  )).data!;
  Future<Map<String, dynamic>> change(
    String ticketId, {
    String eventId = demoEventId,
    bool undo = false,
  }) async => (await dio.post<Map<String, dynamic>>(
    undo ? 'tickets/undo-check-in' : 'tickets/check-in',
    queryParameters: {'event_id': eventId, 'ticket_id': ticketId},
  )).data!;
  Matcher status(int code) => isA<DioException>().having(
    (e) => e.response?.statusCode,
    'HTTP status',
    code,
  );

  test(
    'Event, attendee, verify, check-in and summary contracts match backend JSON shapes',
    () async {
      final events = (await dio.get<List<dynamic>>('checkin/events')).data!;
      expect(events, hasLength(2));
      expect(events.any((e) => e['id'] == unassignedEventId), isFalse);
      expect(events.any((e) => e['id'] == cancelledEventId), isFalse);
      final firstEvent = StaffEvent.fromJson(
        events.first as Map<String, dynamic>,
      );
      expect(firstEvent.canUndoCheckIn, isTrue);
      expect(firstEvent.timezone, 'Asia/Almaty');

      final summary = (await dio.get<Map<String, dynamic>>(
        'checkin/summary',
        queryParameters: {'event_id': demoEventId},
      )).data!;
      expect(summary.keys.toSet(), {'event_id', 'registered', 'checked_in'});
      expect(summary['event_id'], demoEventId);

      final attendees = (await dio.get<List<dynamic>>(
        'checkin/attendees',
        queryParameters: {'event_id': demoEventId, 'limit': 20, 'offset': 0},
      )).data!;
      expect(attendees, isNotEmpty);
      final attendeeRow = attendees.first as Map<String, dynamic>;
      expect(attendeeRow.keys.toSet(), _attendeeResponseKeys);
      expect(attendeeRow.containsKey('qr_token'), isFalse);
      final parsedAttendee = AdmissionTicket.fromAttendee(attendeeRow);
      expect(parsedAttendee.id, attendeeRow['ticket_id']);
      expect(parsedAttendee.status, attendeeRow['ticket_status']);
      expect(parsedAttendee.section, attendeeRow['section']);
      expect(parsedAttendee.row, attendeeRow['row']);
      expect(parsedAttendee.seat, attendeeRow['seat']);

      final verified = await verify('DEMO-VALID');
      expect(verified.keys.toSet(), {'valid', 'status', 'ticket', 'message'});
      final verifiedTicket = verified['ticket'] as Map<String, dynamic>;
      expect(verifiedTicket.keys.toSet(), _ticketResponseKeys);
      expect(verifiedTicket['section'], 'A');
      expect(verifiedTicket['row'], '2');
      expect(verifiedTicket['seat'], '12');

      final gaVerified = await verify('DEMO-GENERAL');
      final gaTicket = gaVerified['ticket'] as Map<String, dynamic>;
      expect(gaTicket['section'], isNull);
      expect(gaTicket['row'], isNull);
      expect(gaTicket['seat'], isNull);

      final checkedIn = await change(verifiedTicket['id'] as String);
      expect(checkedIn.keys.toSet(), _ticketResponseKeys);
      expect(checkedIn['status'], 'checked_in');
    },
  );

  test('Removed checkin/tickets/detail route returns 404', () async {
    final verified = await verify('DEMO-VALID');
    final ticketId = verified['ticket']['id'] as String;
    await expectLater(
      dio.get<dynamic>(
        'checkin/tickets/detail',
        queryParameters: {'event_id': demoEventId, 'ticket_id': ticketId},
      ),
      throwsA(status(404)),
    );
  });

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
      expect(verified['status'], 'valid');
      expect(verified['valid'], isTrue);
      expect(server.summary(demoEventId)['checked_in'], initial);
      final admitted = await change(ticketId);
      expect(admitted['status'], 'checked_in');
      expect(server.summary(demoEventId)['checked_in'], initial + 1);
      expect((await verify('DEMO-VALID'))['status'], 'checked_in');
      await expectLater(change(ticketId), throwsA(status(400)));
      final undone = await change(ticketId, undo: true);
      expect(undone['status'], 'valid');
      expect(server.summary(demoEventId)['checked_in'], initial);
      expect((await verify('DEMO-VALID'))['status'], 'valid');
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
    expect(results.whereType<DioException>().single.response?.statusCode, 400);
  });

  for (final (code, result) in [
    ('DEMO-CANCELLED', 'cancelled'),
    ('DEMO-REFUNDED', 'refunded'),
    ('DEMO-OTHER', 'not_found'),
    (
      'https://biletflow.demo/events/detail?event_id=demo&promo=spring',
      'not_found',
    ),
    ('tampered', 'not_found'),
  ]) {
    test('$code returns $result and never grants admission', () async {
      final response = await verify(code);
      expect(response['status'], result);
      expect(response['valid'], isFalse);
      if (response['ticket'] != null) {
        await expectLater(
          change(response['ticket']['id'] as String),
          throwsA(status(400)),
        );
      }
    });
  }

  test(
    'Campaign links produce a blocked result without a network call',
    () async {
      server.connection = DemoConnection.offline;
      final result = await container
          .read(checkInControllerProvider)
          .verify(
            demoEventId,
            'https://biletflow.demo/events/detail?event_id=demo&promo=spring',
          );
      expect(result.status, 'campaign_qr');
      expect(result.valid, isFalse);
      expect(result.ticket, isNull);
    },
  );

  test('Controller parses verification and the bare changed ticket', () async {
    final controller = container.read(checkInControllerProvider);
    final result = await controller.verify(demoEventId, 'DEMO-VALID');
    expect(result.valid, isTrue);
    expect(result.status, 'valid');
    final admitted = await controller.change(
      demoEventId,
      result.ticket!.id,
      undo: false,
    );
    expect(admitted.status, 'checked_in');
    expect(admitted.checkedInAt, isNotNull);
  });

  test(
    'Manual search and attendee lookup share scanner admission state',
    () async {
      final verified = await verify('DEMO-VALID');
      final ticketId = verified['ticket']['id'] as String;
      await change(ticketId);
      final search = (await dio.get<List<dynamic>>(
        'checkin/attendees',
        queryParameters: {
          'event_id': demoEventId,
          'q': 'guest1@example.test',
          'limit': 20,
          'offset': 0,
        },
      )).data!;
      expect(search, hasLength(1));
      final row = search.first as Map<String, dynamic>;
      expect(row['ticket_id'], ticketId);
      expect(row['ticket_status'], 'checked_in');
      expect(row.containsKey('qr_token'), isFalse);

      final found = await container
          .read(checkInControllerProvider)
          .findAttendee(demoEventId, ticketId);
      expect(found, isNotNull);
      expect(found!.id, ticketId);
      expect(found.status, 'checked_in');
    },
  );

  test(
    'Page-length pagination has no duplicates and stops on a short page',
    () async {
      const pageSize = 4;
      final first = (await dio.get<List<dynamic>>(
        'checkin/attendees',
        queryParameters: {
          'event_id': demoEventId,
          'limit': pageSize,
          'offset': 0,
        },
      )).data!;
      expect(first.length, pageSize);
      final second = (await dio.get<List<dynamic>>(
        'checkin/attendees',
        queryParameters: {
          'event_id': demoEventId,
          'limit': pageSize,
          'offset': first.length,
        },
      )).data!;
      expect(second.length, lessThan(pageSize));
      final all = [...first, ...second];
      expect(all.map((e) => e['ticket_id']).toSet().length, all.length);
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
        throwsA(status(404)),
      );
      final upcoming = await verify('DEMO-OTHER', eventId: upcomingEventId);
      final upcomingTicketId = upcoming['ticket']['id'] as String;
      await change(upcomingTicketId, eventId: upcomingEventId);
      await expectLater(
        change(upcomingTicketId, eventId: upcomingEventId, undo: true),
        throwsA(status(403)),
      );
      server.revoked = true;
      await expectLater(verify('DEMO-VALID'), throwsA(status(404)));
      expect(storage.token, demoToken);
    },
  );

  test('Cancelled event cannot verify or admit a ticket', () async {
    await expectLater(
      dio.get<dynamic>(
        'tickets/verify',
        queryParameters: {
          'event_id': cancelledEventId,
          'qr_token': 'DEMO-VALID',
        },
      ),
      throwsA(status(400)),
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

  test('resolveApiBaseUrl enforces HTTPS in release builds', () {
    expect(
      resolveApiBaseUrl(
        configured: 'https://api.biletflow.kz/api/v1',
        release: true,
      ),
      'https://api.biletflow.kz/api/v1/',
    );
    expect(
      () => resolveApiBaseUrl(
        configured: 'http://localhost:8000/api/v1/',
        release: true,
      ),
      throwsStateError,
    );
    expect(
      resolveApiBaseUrl(
        configured: 'http://localhost:8000/api/v1/',
        release: false,
      ),
      'http://localhost:8000/api/v1/',
    );
  });

  test(
    'sortStaffEvents places active and upcoming events before past ones',
    () {
      final now = DateTime.utc(2026, 11, 23, 12);
      StaffEvent makeEvent(String id, String start, String end) =>
          StaffEvent.fromJson({
            'id': id,
            'organizer_id': 'org',
            'can_undo_check_in': false,
            'title': id,
            'status': 'published',
            'start_time': start,
            'end_time': end,
            'timezone': 'UTC',
            'venue': {'name': 'Hall', 'address': 'Street 1'},
          });
      final sorted = sortStaffEvents([
        makeEvent('past-old', '2026-10-01T10:00:00Z', '2026-10-01T12:00:00Z'),
        makeEvent(
          'future-late',
          '2026-12-10T10:00:00Z',
          '2026-12-10T12:00:00Z',
        ),
        makeEvent('active', '2026-11-23T11:00:00Z', '2026-11-23T14:00:00Z'),
        makeEvent(
          'past-recent',
          '2026-11-20T10:00:00Z',
          '2026-11-20T12:00:00Z',
        ),
        makeEvent(
          'future-soon',
          '2026-11-25T10:00:00Z',
          '2026-11-25T12:00:00Z',
        ),
      ], now: now);
      expect(sorted.map((e) => e.id).toList(), [
        'active',
        'future-soon',
        'future-late',
        'past-recent',
        'past-old',
      ]);
    },
  );
}
