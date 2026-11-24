import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:forui/forui.dart';
import 'package:intl/intl.dart';

import '../../core/localization/locale_provider.dart';
import '../../core/widgets/app_page.dart';
import '../attendees/attendees_screen.dart';
import '../check_in/scanner_screen.dart';
import '../settings/settings_screen.dart';
import 'event.dart';
import 'event_providers.dart';

class EventOverviewScreen extends ConsumerStatefulWidget {
  const EventOverviewScreen({super.key, required this.eventId});
  final String eventId;
  @override
  ConsumerState<EventOverviewScreen> createState() =>
      _EventOverviewScreenState();
}

class _EventOverviewScreenState extends ConsumerState<EventOverviewScreen> {
  int _tab = 0;
  final _attendeesKey = GlobalKey<AttendeesScreenState>();

  @override
  Widget build(BuildContext context) {
    final event = ref.watch(eventProvider(widget.eventId));
    return AppPage(
      title: event.asData?.value.title ?? context.l.overview,
      actions: [
        IconButton(
          tooltip: context.l.settings,
          onPressed: () => openPage(context, const SettingsScreen()),
          icon: const Icon(Icons.account_circle_outlined),
        ),
      ],
      bottomNavigation: NavigationBar(
        selectedIndex: _tab,
        onDestinationSelected: (index) => setState(() => _tab = index),
        destinations: [
          NavigationDestination(
            icon: const Icon(Icons.space_dashboard_outlined),
            selectedIcon: const Icon(Icons.space_dashboard_rounded),
            label: context.l.overviewTab,
          ),
          NavigationDestination(
            icon: const Icon(Icons.qr_code_scanner_rounded),
            label: context.l.scanTab,
          ),
          NavigationDestination(
            icon: const Icon(Icons.people_outline_rounded),
            selectedIcon: const Icon(Icons.people_rounded),
            label: context.l.guestsTab,
          ),
        ],
      ),
      onRefresh: _tab == 0
          ? () async {
              ref.invalidate(summaryProvider(widget.eventId));
              ref.invalidate(eventsProvider);
              try {
                await ref.read(eventProvider(widget.eventId).future);
              } catch (_) {
                /* RequestView displays the error. */
              }
            }
          : _tab == 2
          ? () async => _attendeesKey.currentState?.refresh()
          : null,
      children: [
        RequestView<StaffEvent>(
          value: event,
          retry: () => ref.invalidate(eventsProvider),
          builder: (event) => switch (_tab) {
            1 => ScannerScreen(
              key: ValueKey('scan-${event.id}'),
              event: event,
              embedded: true,
            ),
            2 => AttendeesScreen(
              key: _attendeesKey,
              event: event,
              embedded: true,
            ),
            _ => _Overview(
              event: event,
              onScan: () => setState(() => _tab = 1),
              onGuests: () => setState(() => _tab = 2),
            ),
          },
        ),
      ],
    );
  }
}

class _Overview extends ConsumerWidget {
  const _Overview({
    required this.event,
    required this.onScan,
    required this.onGuests,
  });
  final StaffEvent event;
  final VoidCallback onScan;
  final VoidCallback onGuests;
  @override
  Widget build(BuildContext context, WidgetRef ref) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    spacing: 24,
    children: [
      Row(
        children: [
          Expanded(
            child: Text(
              context.l.overviewTab,
              style: Theme.of(context).textTheme.headlineLarge,
            ),
          ),
          StatusTag(status: event.status),
        ],
      ),
      RequestView<Map<String, dynamic>>(
        value: ref.watch(summaryProvider(event.id)),
        retry: () => ref.invalidate(summaryProvider(event.id)),
        builder: (summary) {
          final registered = summary['registered'] as int,
              checkedIn = summary['checked_in'] as int;
          final remaining = (registered - checkedIn).clamp(0, registered);
          final progress = registered == 0
              ? 0.0
              : (checkedIn / registered).clamp(0.0, 1.0);
          final number = NumberFormat.decimalPattern(
            Localizations.localeOf(context).languageCode,
          );
          return Semantics(
            button: true,
            label: '${context.l.attendance}: ${context.l.guestsTab}',
            child: InfoCard(
              onTap: onGuests,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                spacing: 20,
                children: [
                  Row(
                    children: [
                      Icon(
                        Icons.people_outline_rounded,
                        color: context.theme.colors.primary,
                        size: 20,
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          context.l.attendance,
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                      ),
                      Icon(
                        Icons.chevron_right_rounded,
                        color: context.theme.colors.mutedForeground,
                        size: 20,
                      ),
                    ],
                  ),
                  Wrap(
                    crossAxisAlignment: WrapCrossAlignment.end,
                    spacing: 12,
                    children: [
                      Text(
                        number.format(checkedIn),
                        style: TextStyle(
                          fontSize: 56,
                          height: 1,
                          letterSpacing: -2,
                          fontWeight: FontWeight.w600,
                          color: context.theme.colors.primary,
                        ),
                      ),
                      Padding(
                        padding: const EdgeInsets.only(bottom: 4),
                        child: Text(
                          context.l.admittedLabel,
                          style: TextStyle(
                            color: context.theme.colors.mutedForeground,
                          ),
                        ),
                      ),
                    ],
                  ),
                  Semantics(
                    label: context.l.ofRegistered(number.format(registered)),
                    child: LinearProgressIndicator(
                      value: progress,
                      minHeight: 6,
                      borderRadius: BorderRadius.circular(3),
                      color: context.theme.colors.primary,
                      backgroundColor: context.theme.colors.secondary,
                    ),
                  ),
                  Row(
                    children: [
                      Expanded(
                        child: _Count(
                          label: context.l.registered,
                          value: number.format(registered),
                        ),
                      ),
                      Expanded(
                        child: _Count(
                          label: context.l.remaining,
                          value: number.format(remaining),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          );
        },
      ),
      FButton(
        builder: fitButtonLabel,
        size: .lg,
        onPress: onScan,
        prefix: const Icon(Icons.qr_code_scanner_rounded),
        child: Text(context.l.scanTicket),
      ),
      Text(
        context.l.eventDetails,
        style: Theme.of(context).textTheme.titleMedium,
      ),
      DetailRow(
        icon: Icons.calendar_today_outlined,
        title: eventDatePart(
          context,
          event.startsAt,
          event.timezone,
          'EEEE, d MMMM',
        ),
        subtitle:
            '${eventDatePart(context, event.startsAt, event.timezone, 'HH:mm')}  •  ${event.timezone}',
      ),
      DetailRow(
        icon: Icons.location_on_outlined,
        title: event.venue,
        subtitle: event.address,
      ),
    ],
  );
}

class _Count extends StatelessWidget {
  const _Count({required this.label, required this.value});
  final String label, value;
  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    spacing: 4,
    children: [
      Text(value, style: Theme.of(context).textTheme.titleLarge),
      Text(label, style: Theme.of(context).textTheme.bodySmall),
    ],
  );
}
