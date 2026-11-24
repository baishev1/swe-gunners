import 'dart:convert';
import 'dart:typed_data';

import 'package:biletflow_staff/app.dart';
import 'package:biletflow_staff/core/localization/locale_provider.dart';
import 'package:biletflow_staff/core/network/api_client.dart';
import 'package:biletflow_staff/core/network/mock_api_adapter.dart';
import 'package:biletflow_staff/core/network/mock_fixtures.dart';
import 'package:biletflow_staff/core/storage/token_storage.dart';
import 'package:biletflow_staff/core/theme/app_theme.dart';
import 'package:biletflow_staff/core/widgets/app_page.dart';
import 'package:biletflow_staff/features/check_in/ticket_screen.dart';
import 'package:biletflow_staff/features/events/event.dart';
import 'package:biletflow_staff/l10n/app_localizations.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:forui/forui.dart';

import 'test_storage.dart';

class _FixedLocale extends LocaleController {
  _FixedLocale(this._locale);
  final Locale _locale;
  @override
  Locale? build() => _locale;
}

class _RecordingAdapter implements HttpClientAdapter {
  _RecordingAdapter(this._inner);
  final HttpClientAdapter _inner;
  final List<String> paths = [];

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) {
    paths.add(options.uri.path);
    return _inner.fetch(options, requestStream, cancelFuture);
  }

  @override
  void close({bool force = false}) => _inner.close(force: force);
}

class _LambdaAdapter implements HttpClientAdapter {
  _LambdaAdapter(this._handler);
  final Future<ResponseBody> Function(RequestOptions) _handler;
  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) => _handler(options);
  @override
  void close({bool force = false}) {}
}

Future<
  ({MemoryTokenStorage storage, MockServer server, _RecordingAdapter recorder})
>
_startRealApp(WidgetTester tester, {bool signedIn = true}) async {
  final storage = MemoryTokenStorage(signedIn ? demoToken : null);
  final server = MockServer(latency: Duration.zero);
  final recorder = _RecordingAdapter(MockApiAdapter(server));
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        useMockApiProvider.overrideWithValue(false),
        httpClientAdapterProvider.overrideWithValue(recorder),
        tokenStorageProvider.overrideWithValue(storage),
        localeProvider.overrideWith(() => _FixedLocale(const Locale('en'))),
      ],
      child: const BiletflowApp(),
    ),
  );
  await tester.pumpAndSettle();
  return (storage: storage, server: server, recorder: recorder);
}

Future<void> _tapText(WidgetTester tester, String label) async {
  final target = find.text(label).first;
  await tester.ensureVisible(target);
  await tester.tap(target);
  await tester.pumpAndSettle();
}

void main() {
  testWidgets(
    'Real mode shows attendance summary, Guests search, attendee detail, check-in and undo without removed route',
    (tester) async {
      final env = await _startRealApp(tester);
      // No demo pill in real mode.
      expect(find.text('Demo'), findsNothing);

      await tester.tap(find.byKey(const ValueKey(demoEventId)));
      await tester.pumpAndSettle();

      // Summary card renders in real mode (2 checked in, 4 registered, 2 remaining).
      expect(find.text('Attendance'), findsOneWidget);
      expect(find.text('Registered'), findsOneWidget);
      expect(find.text('Not arrived'), findsOneWidget);
      expect(find.text('4'), findsOneWidget);
      expect(find.text('2'), findsNWidgets(2));

      // Guests destination is visible in real mode.
      expect(find.text('Guests'), findsOneWidget);
      await _tapText(tester, 'Guests');

      // Search by email using backend EventAttendeeResponse rows.
      await tester.enterText(find.byType(EditableText), 'guest1@example.test');
      await tester.pump(const Duration(milliseconds: 350));
      await tester.pumpAndSettle();
      expect(find.text('Аружан Демо'), findsOneWidget);
      expect(find.text('Данияр Демо'), findsNothing);

      // Tap guest to open detail, admit, then undo.
      await _tapText(tester, 'Аружан Демо');
      expect(find.text('Valid ticket'), findsOneWidget);
      await _tapText(tester, 'Check in');
      expect(find.text('Check-in recorded'), findsOneWidget);

      await _tapText(tester, 'Undo check-in');
      await _tapText(tester, 'Confirm');
      expect(find.text('Check-in reversed'), findsOneWidget);

      // Verify the removed checkin/tickets/detail route was never called.
      expect(
        env.recorder.paths.any((p) => p.contains('checkin/tickets/detail')),
        isFalse,
      );
      expect(
        env.recorder.paths.any((p) => p.endsWith('checkin/attendees')),
        isTrue,
      );
      expect(
        env.recorder.paths.any((p) => p.endsWith('checkin/summary')),
        isTrue,
      );
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'Failed detail load shows error and retry, never Invalid ticket',
    (tester) async {
      final event = StaffEvent.fromJson(eventFixtures().first);
      final adapter = _LambdaAdapter(
        (_) async => ResponseBody.fromString(
          jsonEncode({'detail': 'service_unavailable'}),
          503,
          headers: {
            Headers.contentTypeHeader: [Headers.jsonContentType],
          },
        ),
      );
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            useMockApiProvider.overrideWithValue(false),
            httpClientAdapterProvider.overrideWithValue(adapter),
            tokenStorageProvider.overrideWithValue(
              MemoryTokenStorage(demoToken),
            ),
            localeProvider.overrideWith(() => _FixedLocale(const Locale('en'))),
          ],
          child: MaterialApp(
            locale: const Locale('en'),
            supportedLocales: AppLocalizations.supportedLocales,
            localizationsDelegates: const [
              AppLocalizations.delegate,
              ...FLocalizations.localizationsDelegates,
            ],
            builder: (context, child) =>
                FTheme(data: staffTheme(Brightness.light), child: child!),
            home: TicketScreen(
              event: event,
              ticketId: '019a2000-0000-7000-8000-000000000001',
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(
        find.text('Service unavailable. Please try again.'),
        findsOneWidget,
      );
      expect(find.text('Retry'), findsOneWidget);
      expect(find.text('Invalid ticket'), findsNothing);
      expect(find.byIcon(Icons.block_rounded), findsNothing);
    },
  );

  testWidgets(
    'Missing attendee row shows Ticket not found, not Invalid ticket',
    (tester) async {
      final event = StaffEvent.fromJson(eventFixtures().first);
      final adapter = _LambdaAdapter(
        (_) async => ResponseBody.fromString(
          jsonEncode(<dynamic>[]),
          200,
          headers: {
            Headers.contentTypeHeader: [Headers.jsonContentType],
          },
        ),
      );
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            useMockApiProvider.overrideWithValue(false),
            httpClientAdapterProvider.overrideWithValue(adapter),
            tokenStorageProvider.overrideWithValue(
              MemoryTokenStorage(demoToken),
            ),
            localeProvider.overrideWith(() => _FixedLocale(const Locale('en'))),
          ],
          child: MaterialApp(
            locale: const Locale('en'),
            supportedLocales: AppLocalizations.supportedLocales,
            localizationsDelegates: const [
              AppLocalizations.delegate,
              ...FLocalizations.localizationsDelegates,
            ],
            builder: (context, child) =>
                FTheme(data: staffTheme(Brightness.light), child: child!),
            home: TicketScreen(
              event: event,
              ticketId: '019a2000-0000-7000-8000-999999999999',
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('Ticket not found'), findsOneWidget);
      expect(find.text('Invalid ticket'), findsNothing);
    },
  );

  testWidgets(
    'Error mapping never blames storage for parse errors and localizes 422/order statuses in EN, KK, RU',
    (tester) async {
      for (final locale in const [Locale('en'), Locale('kk'), Locale('ru')]) {
        late BuildContext captured;
        await tester.pumpWidget(
          MaterialApp(
            locale: locale,
            supportedLocales: AppLocalizations.supportedLocales,
            localizationsDelegates: const [
              AppLocalizations.delegate,
              ...FLocalizations.localizationsDelegates,
            ],
            home: Builder(
              builder: (context) {
                captured = context;
                return const SizedBox.shrink();
              },
            ),
          ),
        );
        await tester.pumpAndSettle();

        final parseMsg = errorMessage(captured, const FormatException('bad'));
        expect(parseMsg, captured.l.genericError);
        expect(parseMsg, isNot(captured.l.storageError));

        final req = RequestOptions(path: 'checkin/attendees');
        final validation422 = DioException.badResponse(
          statusCode: 422,
          requestOptions: req,
          response: Response<dynamic>(
            requestOptions: req,
            statusCode: 422,
            data: {
              'detail': [
                {'msg': 'field required'},
              ],
            },
          ),
        );
        expect(
          errorMessage(captured, validation422),
          captured.l.validationError,
        );

        final string422 = DioException.badResponse(
          statusCode: 422,
          requestOptions: req,
          response: Response<dynamic>(
            requestOptions: req,
            statusCode: 422,
            data: {'detail': 'Invalid query parameter'},
          ),
        );
        expect(errorMessage(captured, string422), 'Invalid query parameter');

        expect(statusLabel(captured, 'pending'), captured.l.pending);
        expect(statusLabel(captured, 'invalid_order'), captured.l.invalidOrder);
        expect(statusLabel(captured, 'not_found'), captured.l.ticketNotFound);
        expect(statusLabel(captured, 'pending'), isNot(captured.l.invalid));
        expect(
          statusLabel(captured, 'invalid_order'),
          isNot(captured.l.invalid),
        );
      }
    },
  );

  testWidgets('Real mode 401 clears stored token and returns to Sign in', (
    tester,
  ) async {
    final env = await _startRealApp(tester);
    expect(find.text('Your events'), findsOneWidget);

    env.server.expired = true;
    await tester.tap(find.byTooltip('Settings'));
    await tester.pumpAndSettle();

    // auth/me returns 401 -> session invalidated -> LoginScreen shown.
    expect(env.storage.token, isNull);
    expect(find.text('Sign in'), findsOneWidget);
    expect(find.text('Your events'), findsNothing);
  });

  testWidgets('Settings derives avatar initials from the account name', (
    tester,
  ) async {
    final storage = MemoryTokenStorage(demoToken);
    final adapter = _LambdaAdapter((request) async {
      final path = request.uri.path;
      if (path.endsWith('auth/me')) {
        return ResponseBody.fromString(
          jsonEncode({
            'id': 'u1',
            'email': 'bota@biletflow.kz',
            'full_name': 'Bota Kassymova',
            'role': 'organizer',
            'is_email_verified': true,
          }),
          200,
          headers: {
            Headers.contentTypeHeader: [Headers.jsonContentType],
          },
        );
      }
      return ResponseBody.fromString(
        jsonEncode(<dynamic>[]),
        200,
        headers: {
          Headers.contentTypeHeader: [Headers.jsonContentType],
        },
      );
    });
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          useMockApiProvider.overrideWithValue(false),
          httpClientAdapterProvider.overrideWithValue(adapter),
          tokenStorageProvider.overrideWithValue(storage),
          localeProvider.overrideWith(() => _FixedLocale(const Locale('en'))),
        ],
        child: const BiletflowApp(),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byTooltip('Settings'));
    await tester.pumpAndSettle();

    expect(find.text('BK'), findsOneWidget);
    expect(find.text('AD'), findsNothing);
    expect(find.text('Bota Kassymova'), findsOneWidget);
  });

  testWidgets(
    'Real mode displays assigned seat for seated tickets and General admission for unseated tickets',
    (tester) async {
      await _startRealApp(tester);
      await tester.tap(find.byKey(const ValueKey(demoEventId)));
      await tester.pumpAndSettle();

      // Open seated guest from Guests list (EventAttendeeResponse).
      await _tapText(tester, 'Guests');
      await _tapText(tester, 'Аружан Демо');
      expect(find.text('A / 2 / 12'), findsOneWidget);
      expect(find.text('General admission'), findsNothing);
      await tester.tap(find.byTooltip('Back'));
      await tester.pumpAndSettle();

      // Open general-admission guest from Guests list.
      await _tapText(tester, 'Kai Demo');
      expect(find.text('General admission'), findsOneWidget);
      expect(find.text('A / 2 / 12'), findsNothing);
      await tester.tap(find.byTooltip('Back'));
      await tester.pumpAndSettle();

      // Verify seated and general-admission tickets via Scan -> Verify (TicketResponse).
      await _tapText(tester, 'Scan');
      await _tapText(tester, 'Enter code manually');
      await tester.enterText(find.byType(EditableText).first, 'DEMO-VALID');
      await _tapText(tester, 'Verify ticket');
      expect(find.text('A / 2 / 12'), findsOneWidget);
      await tester.tap(find.byTooltip('Back'));
      await tester.pumpAndSettle();

      await _tapText(tester, 'Enter code manually');
      await tester.enterText(find.byType(EditableText).first, 'DEMO-GENERAL');
      await _tapText(tester, 'Verify ticket');
      expect(find.text('General admission'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );
}
