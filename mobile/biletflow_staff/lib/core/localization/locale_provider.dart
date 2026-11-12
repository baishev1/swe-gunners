import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:timezone/data/latest.dart' as tzdata;
import 'package:timezone/timezone.dart' as tz;

import '../../l10n/app_localizations.dart';

final localeProvider = NotifierProvider<LocaleController, Locale?>(
  LocaleController.new,
);

class LocaleController extends Notifier<Locale?> {
  @override
  Locale? build() => null;
  void select(String code) => state = Locale(code);
}

extension LocalizedContext on BuildContext {
  AppLocalizations get l => AppLocalizations.of(this);
}

bool _timezonesInitialized = false;
String eventDate(BuildContext context, String timestamp, String zone) {
  if (!_timezonesInitialized) {
    tzdata.initializeTimeZones();
    _timezonesInitialized = true;
  }
  final local = tz.TZDateTime.from(
    DateTime.parse(timestamp),
    tz.getLocation(zone),
  );
  return '${DateFormat.yMMMd(Localizations.localeOf(context).languageCode).add_Hm().format(local)} · $zone';
}

String statusLabel(BuildContext context, String code) => switch (code) {
  'valid' => context.l.valid,
  'checked_in' => context.l.checked_in,
  'cancelled' => context.l.cancelled,
  'refunded' => context.l.refunded,
  'wrong_event' => context.l.wrong_event,
  'campaign_qr' => context.l.campaign_qr,
  'published' => context.l.published,
  _ => context.l.invalid,
};

String eventDatePart(
  BuildContext context,
  String timestamp,
  String zone,
  String pattern,
) {
  if (!_timezonesInitialized) {
    tzdata.initializeTimeZones();
    _timezonesInitialized = true;
  }
  final local = tz.TZDateTime.from(
    DateTime.parse(timestamp),
    tz.getLocation(zone),
  );
  return DateFormat(
    pattern,
    Localizations.localeOf(context).languageCode,
  ).format(local);
}
