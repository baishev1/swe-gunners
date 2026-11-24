import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:forui/forui.dart';

import '../../core/localization/locale_provider.dart';
import '../../core/widgets/app_page.dart';
import '../settings/settings_screen.dart';
import 'event.dart';
import 'event_overview_screen.dart';
import 'event_providers.dart';

class EventsScreen extends ConsumerWidget {
  const EventsScreen({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) => AppPage(
    title: 'Biletflow',
    back: false,
    actions: [
      IconButton(
        tooltip: context.l.settings,
        onPressed: () => openPage(context, const SettingsScreen()),
        icon: const Icon(Icons.account_circle_outlined),
      ),
    ],
    onRefresh: () async {
      ref.invalidate(eventsProvider);
      try {
        await ref.read(eventsProvider.future);
      } catch (_) {
        /* RequestView displays the error. */
      }
    },
    children: [
      const SizedBox(height: 4),
      Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        spacing: 8,
        children: [
          Text(
            context.l.yourEvents,
            style: Theme.of(context).textTheme.headlineLarge,
          ),
          Text(
            context.l.chooseEvent,
            style: TextStyle(color: context.theme.colors.mutedForeground),
          ),
        ],
      ),
      RequestView<List<StaffEvent>>(
        value: ref.watch(eventsProvider),
        retry: () => ref.invalidate(eventsProvider),
        builder: (events) => Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          spacing: 16,
          children: [
            if (events.isEmpty)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 48),
                child: Column(
                  spacing: 16,
                  children: [
                    Icon(
                      Icons.event_available_outlined,
                      size: 48,
                      color: context.theme.colors.mutedForeground,
                    ),
                    Text(context.l.noEvents, textAlign: TextAlign.center),
                    FButton(
                      builder: fitButtonLabel,
                      size: .lg,
                      variant: FButtonVariant.outline,
                      prefix: const Icon(Icons.refresh_rounded),
                      onPress: () => ref.invalidate(eventsProvider),
                      child: Text(context.l.refresh),
                    ),
                  ],
                ),
              ),
            for (final event in events)
              Semantics(
                button: true,
                label: '${context.l.overview}: ${event.title}',
                child: InfoCard(
                  key: ValueKey(event.id),
                  onTap: () =>
                      openPage(context, EventOverviewScreen(eventId: event.id)),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    spacing: 20,
                    children: [
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Container(
                            constraints: const BoxConstraints(minWidth: 56),
                            padding: const EdgeInsets.symmetric(
                              horizontal: 8,
                              vertical: 9,
                            ),
                            decoration: BoxDecoration(
                              color: context.theme.colors.secondary,
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Column(
                              children: [
                                Text(
                                  eventDatePart(
                                    context,
                                    event.startsAt,
                                    event.timezone,
                                    'MMM',
                                  ).toUpperCase(),
                                  maxLines: 1,
                                  style: TextStyle(
                                    fontSize: 10,
                                    fontWeight: FontWeight.w700,
                                    color: context.theme.colors.primary,
                                  ),
                                ),
                                Text(
                                  eventDatePart(
                                    context,
                                    event.startsAt,
                                    event.timezone,
                                    'd',
                                  ),
                                  maxLines: 1,
                                  style: TextStyle(
                                    fontSize: 26,
                                    fontWeight: FontWeight.w600,
                                    height: 1.2,
                                    color: context.theme.colors.foreground,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(width: 16),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              spacing: 6,
                              children: [
                                Text(
                                  event.title,
                                  style: Theme.of(context).textTheme.titleLarge,
                                ),
                                Text(
                                  eventDatePart(
                                    context,
                                    event.startsAt,
                                    event.timezone,
                                    'EEEE, HH:mm',
                                  ),
                                  style: Theme.of(context).textTheme.bodySmall,
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(width: 8),
                          Icon(
                            Icons.chevron_right_rounded,
                            color: context.theme.colors.mutedForeground,
                          ),
                        ],
                      ),
                      Row(
                        children: [
                          Icon(
                            Icons.location_on_outlined,
                            size: 17,
                            color: context.theme.colors.mutedForeground,
                          ),
                          const SizedBox(width: 6),
                          Expanded(
                            child: Text(
                              event.venue,
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                              style: Theme.of(context).textTheme.bodySmall,
                            ),
                          ),
                          const SizedBox(width: 8),
                          StatusTag(status: event.status),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
    ],
  );
}
