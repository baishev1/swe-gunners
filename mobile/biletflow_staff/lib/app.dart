import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:forui/forui.dart';

import 'core/localization/locale_provider.dart';
import 'features/auth/auth_gate.dart';
import 'core/theme/app_theme.dart';
import 'l10n/app_localizations.dart';

class BiletflowApp extends ConsumerWidget {
  const BiletflowApp({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final light = staffTheme(Brightness.light);
    final dark = staffTheme(Brightness.dark);
    return MaterialApp(
      title: 'Biletflow Staff',
      debugShowCheckedModeBanner: false,
      locale: ref.watch(localeProvider),
      supportedLocales: AppLocalizations.supportedLocales,
      localizationsDelegates: const [
        AppLocalizations.delegate,
        ...FLocalizations.localizationsDelegates,
      ],
      theme: materialTheme(light),
      darkTheme: materialTheme(dark),
      builder: (context, child) => FTheme(
        data: Theme.brightnessOf(context) == Brightness.dark ? dark : light,
        child: FToaster(child: FTooltipGroup(child: child!)),
      ),
      home: const AuthGate(),
    );
  }
}
