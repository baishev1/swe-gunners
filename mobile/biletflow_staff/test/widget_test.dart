import 'package:biletflow_staff/app.dart';
import 'package:biletflow_staff/core/localization/locale_provider.dart';
import 'package:biletflow_staff/core/network/mock_api_adapter.dart';
import 'package:biletflow_staff/core/network/mock_fixtures.dart';
import 'package:biletflow_staff/core/storage/token_storage.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'test_storage.dart';

class EnglishLocale extends LocaleController {
  @override
  Locale? build() => const Locale('en');
}

Future<MemoryTokenStorage> start(
  WidgetTester tester, {
  bool signedIn = false,
}) async {
  final storage = MemoryTokenStorage(signedIn ? demoToken : null);
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        tokenStorageProvider.overrideWithValue(storage),
        mockServerProvider.overrideWithValue(
          MockServer(latency: Duration.zero),
        ),
        localeProvider.overrideWith(EnglishLocale.new),
      ],
      child: const BiletflowApp(),
    ),
  );
  await tester.pumpAndSettle();
  return storage;
}

Future<void> tap(WidgetTester tester, String label) async {
  final target = find.text(label).first;
  await tester.ensureVisible(target);
  await tester.tap(target);
  await tester.pumpAndSettle();
}

Future<void> event(WidgetTester tester) async {
  await tester.tap(find.byKey(const ValueKey(demoEventId)));
  await tester.pumpAndSettle();
}

Future<void> scan(WidgetTester tester, String code) async {
  await tap(tester, 'Enter code manually');
  await tester.enterText(find.byType(EditableText).first, code);
  await tap(tester, 'Verify ticket');
}

void main() {
  testWidgets('Demo sign in opens assigned events', (tester) async {
    final storage = await start(tester);
    await tap(tester, 'Sign in');
    expect(find.text('Your events'), findsOneWidget);
    expect(storage.token, demoToken);
    expect(find.text('Private Partner Summit'), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Locale changes without resetting the login form', (
    tester,
  ) async {
    await start(tester);
    await tester.tap(find.byTooltip('Language'));
    await tester.pumpAndSettle();
    await tap(tester, 'Қазақша');
    expect(find.text('Кіру'), findsOneWidget);
    await tap(tester, 'Русский');
    expect(find.text('Войти'), findsOneWidget);
    await tap(tester, 'English');
    expect(find.text('Sign in'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Reset password displays generic demo confirmation', (
    tester,
  ) async {
    await start(tester);
    await tap(tester, 'Forgot password?');
    await tap(tester, 'Send reset link');
    expect(find.textContaining('If this account exists'), findsOneWidget);
  });

  testWidgets('Manual scan admits, rejects duplicate, and allows undo', (
    tester,
  ) async {
    await start(tester, signedIn: true);
    await event(tester);
    await tap(tester, 'Scan');
    await scan(tester, 'DEMO-VALID');
    expect(find.text('Valid ticket'), findsOneWidget);
    await tap(tester, 'Check in');
    expect(find.text('Check-in recorded'), findsOneWidget);
    await tap(tester, 'Scan next ticket');
    await scan(tester, 'DEMO-VALID');
    expect(find.text('Already used'), findsOneWidget);
    expect(find.text('Check in'), findsNothing);
    await tap(tester, 'Undo check-in');
    await tap(tester, 'Confirm');
    expect(find.text('Check-in reversed'), findsOneWidget);
    expect(find.text('Check in'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Guests tab searches live and opens the same admission record', (
    tester,
  ) async {
    await start(tester, signedIn: true);
    await event(tester);
    await tap(tester, 'Guests');
    await tester.enterText(find.byType(EditableText), 'guest1@example.test');
    await tester.pump(const Duration(milliseconds: 350));
    await tester.pumpAndSettle();
    expect(find.text('Аружан Демо'), findsOneWidget);
    expect(find.text('Данияр Демо'), findsNothing);
    await tap(tester, 'Аружан Демо');
    await tap(tester, 'Check in');
    expect(find.text('Check-in recorded'), findsOneWidget);
    await tester.tap(find.byTooltip('Back'));
    await tester.pumpAndSettle();
    expect(find.text('Already used'), findsOneWidget);
  });

  testWidgets('Logout confirms and removes protected navigation', (
    tester,
  ) async {
    final storage = await start(tester, signedIn: true);
    await tester.tap(find.byTooltip('Settings'));
    await tester.pumpAndSettle();
    await tap(tester, 'Log out');
    await tap(tester, 'Confirm');
    expect(storage.token, isNull);
    expect(find.text('Sign in'), findsOneWidget);
    expect(find.byTooltip('Back'), findsNothing);
    expect(find.text('Your events'), findsNothing);
  });

  testWidgets('Expired session removes the event workspace and demo routes', (
    tester,
  ) async {
    final storage = await start(tester, signedIn: true);
    await event(tester);
    await tester.tap(find.byTooltip('Settings'));
    await tester.pumpAndSettle();
    await tap(tester, 'Demo controls');
    await tap(tester, 'Expire session');
    expect(storage.token, isNull);
    expect(find.text('Sign in'), findsOneWidget);
    expect(find.text('Your events'), findsNothing);
  });

  testWidgets('System back pops the event workspace', (tester) async {
    await start(tester, signedIn: true);
    await event(tester);
    await tester.binding.handlePopRoute();
    await tester.pumpAndSettle();
    expect(find.text('Your events'), findsOneWidget);
  });

  testWidgets('Narrow screens and large text keep primary controls reachable', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(320, 720);
    tester.view.devicePixelRatio = 1;
    tester.platformDispatcher.textScaleFactorTestValue = 1.4;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
    await start(tester);
    await tap(tester, 'Sign in');
    await event(tester);
    await tap(tester, 'Scan');
    await scan(tester, 'DEMO-VALID');
    await tap(tester, 'Check in');
    expect(find.text('Check-in recorded'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
