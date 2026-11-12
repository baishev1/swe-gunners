import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:forui/forui.dart';

import '../../core/localization/locale_provider.dart';
import '../../core/network/api_client.dart';
import '../../core/network/mock_api_adapter.dart';
import '../../core/network/mock_fixtures.dart';
import '../../core/widgets/app_page.dart';
import '../auth/session_controller.dart';
import '../events/event_providers.dart';

class SettingsScreen extends ConsumerStatefulWidget {
  const SettingsScreen({super.key});
  @override
  ConsumerState<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends ConsumerState<SettingsScreen> {
  Object? _error;
  bool _busy = false;
  Future<void> _logout() async {
    final confirmed = await showDialog<bool>(
      context: context,
      useRootNavigator: false,
      builder: (context) => AlertDialog(
        title: Text(context.l.logoutConfirm),
        content: Text(context.l.logoutHint),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text(context.l.cancel),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text(context.l.confirm),
          ),
        ],
      ),
    );
    if (!mounted || confirmed != true) return;
    setState(() => _busy = true);
    try {
      await ref.read(sessionProvider.notifier).logout();
    } catch (error) {
      if (mounted) setState(() => _error = error);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => AppPage(
    title: context.l.settings,
    children: [
      Text(context.l.account, style: Theme.of(context).textTheme.headlineLarge),
      RequestView<Map<String, dynamic>>(
        value: ref.watch(accountProvider),
        retry: () => ref.invalidate(accountProvider),
        builder: (account) => InfoCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            spacing: 18,
            children: [
              CircleAvatar(
                radius: 28,
                backgroundColor: context.theme.colors.secondary,
                foregroundColor: context.theme.colors.primary,
                child: const Text(
                  'AD',
                  style: TextStyle(fontWeight: FontWeight.w600),
                ),
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                spacing: 4,
                children: [
                  Text(
                    account['full_name'] as String,
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  Text(
                    account['email'] as String,
                    style: TextStyle(
                      color: context.theme.colors.mutedForeground,
                    ),
                  ),
                ],
              ),
              Text(
                context.l.signedInAs,
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ),
        ),
      ),
      Text(
        context.l.preferences,
        style: Theme.of(context).textTheme.titleMedium,
      ),
      Material(
        color: context.theme.colors.card,
        borderRadius: BorderRadius.circular(16),
        clipBehavior: Clip.antiAlias,
        child: Column(
          children: [
            ListTile(
              minVerticalPadding: 14,
              leading: const Icon(Icons.language_rounded),
              title: Text(context.l.language),
              subtitle: Text(switch (Localizations.localeOf(
                context,
              ).languageCode) {
                'kk' => 'Қазақша',
                'ru' => 'Русский',
                _ => 'English',
              }),
              trailing: const Icon(Icons.chevron_right_rounded),
              onTap: () => appSheet<void>(
                context,
                title: context.l.language,
                child: const LanguagePicker(),
              ),
            ),
            if (useMockApi) ...[
              Divider(
                height: 1,
                indent: 20,
                endIndent: 20,
                color: context.theme.colors.border,
              ),
              ListTile(
                minVerticalPadding: 14,
                leading: const Icon(Icons.science_outlined),
                title: Text(context.l.demoControls),
                subtitle: Text(context.l.demoToolsHint),
                trailing: const Icon(Icons.chevron_right_rounded),
                onTap: () => openPage(context, const DemoToolsScreen()),
              ),
            ],
          ],
        ),
      ),
      if (_error != null) ErrorNotice(error: _error!),
      TextButton.icon(
        onPressed: _busy ? null : _logout,
        style: TextButton.styleFrom(
          foregroundColor: context.theme.colors.error,
          minimumSize: const Size(48, 52),
        ),
        icon: const Icon(Icons.logout_rounded, size: 20),
        label: Text(context.l.logout),
      ),
    ],
  );
}

class DemoToolsScreen extends ConsumerStatefulWidget {
  const DemoToolsScreen({super.key});
  @override
  ConsumerState<DemoToolsScreen> createState() => _DemoToolsScreenState();
}

class _DemoToolsScreenState extends ConsumerState<DemoToolsScreen> {
  void _refreshData() {
    ref.invalidate(eventsProvider);
    ref.invalidate(eventProvider);
    ref.invalidate(summaryProvider);
    ref.invalidate(accountProvider);
  }

  @override
  Widget build(BuildContext context) {
    final server = ref.read(mockServerProvider);
    return AppPage(
      title: context.l.demoControls,
      children: [
        Text(
          context.l.demoToolsHint,
          style: TextStyle(color: context.theme.colors.mutedForeground),
        ),
        RadioGroup<DemoConnection>(
          groupValue: server.connection,
          onChanged: (mode) {
            setState(() => server.connection = mode!);
            _refreshData();
          },
          child: Column(
            children: [
              for (final (mode, label) in [
                (DemoConnection.normal, context.l.normal),
                (DemoConnection.offline, context.l.offlineMode),
                (DemoConnection.serverError, context.l.serverMode),
              ])
                RadioListTile<DemoConnection>(value: mode, title: Text(label)),
            ],
          ),
        ),
        FSwitch(
          label: Text(context.l.emptyAssignments),
          value: server.emptyAssignments,
          onChange: (value) {
            setState(() => server.emptyAssignments = value);
            _refreshData();
          },
        ),
        FSwitch(
          label: Text(context.l.revokeAssignment),
          value: server.revoked,
          onChange: (value) {
            setState(() => server.revoked = value);
            _refreshData();
          },
        ),
        FSwitch(
          label: Text(context.l.cancelEventDemo),
          value:
              server.events.firstWhere(
                (e) => e['id'] == demoEventId,
              )['status'] ==
              'cancelled',
          onChange: (value) {
            setState(
              () => server.events.firstWhere(
                (e) => e['id'] == demoEventId,
              )['status'] = value ? 'cancelled' : 'published',
            );
            _refreshData();
          },
        ),
        FButton(
          builder: fitButtonLabel,
          size: .lg,
          variant: FButtonVariant.outline,
          onPress: () async {
            server.connection = DemoConnection.normal;
            server.expired = true;
            try {
              await ref.read(dioProvider).get<dynamic>('auth/me');
            } catch (_) {
              /* Shared 401 handler clears the session. */
            }
          },
          child: Text(context.l.expireSession),
        ),
        FButton(
          builder: fitButtonLabel,
          size: .lg,
          variant: FButtonVariant.outline,
          onPress: () {
            setState(server.reset);
            _refreshData();
          },
          child: Text(context.l.resetDemo),
        ),
      ],
    );
  }
}
