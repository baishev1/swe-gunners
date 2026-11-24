import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:forui/forui.dart';

import '../localization/locale_provider.dart';
import '../network/mock_api_adapter.dart';
import '../theme/app_theme.dart';

class AppPage extends ConsumerWidget {
  const AppPage({
    super.key,
    required this.title,
    required this.children,
    this.actions = const [],
    this.back = true,
    this.footer,
    this.bottomNavigation,
    this.onRefresh,
  });
  final String title;
  final List<Widget> children, actions;
  final bool back;
  final Widget? footer, bottomNavigation;
  final Future<void> Function()? onRefresh;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    Widget content = SingleChildScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
      keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
      padding: const EdgeInsets.fromLTRB(24, 12, 24, 28),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 600),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            spacing: 20,
            children: children,
          ),
        ),
      ),
    );
    if (onRefresh != null) {
      content = RefreshIndicator(onRefresh: onRefresh!, child: content);
    }
    return Scaffold(
      appBar: AppBar(
        automaticallyImplyLeading: false,
        leading: back && Navigator.of(context).canPop()
            ? IconButton(
                tooltip: context.l.back,
                onPressed: () => Navigator.of(context).maybePop(),
                icon: const Icon(Icons.arrow_back_rounded),
              )
            : null,
        titleSpacing: back && Navigator.of(context).canPop() ? 0 : 24,
        title: Text(title, maxLines: 1, overflow: TextOverflow.ellipsis),
        actions: [
          if (ref.watch(useMockApiProvider)) const DemoIndicator(),
          ...actions,
          const SizedBox(width: 12),
        ],
      ),
      body: SafeArea(
        top: false,
        bottom: footer == null && bottomNavigation == null,
        child: content,
      ),
      bottomNavigationBar: footer == null && bottomNavigation == null
          ? null
          : Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                if (footer != null)
                  Container(
                    decoration: BoxDecoration(
                      color: Theme.of(context).cardColor,
                      border: Border(
                        top: BorderSide(color: Theme.of(context).dividerColor),
                      ),
                    ),
                    child: SafeArea(
                      top: false,
                      bottom: bottomNavigation == null,
                      child: Padding(
                        padding: const EdgeInsets.fromLTRB(24, 16, 24, 16),
                        child: Center(
                          child: ConstrainedBox(
                            constraints: const BoxConstraints(maxWidth: 600),
                            child: footer!,
                          ),
                        ),
                      ),
                    ),
                  ),
                if (bottomNavigation != null)
                  DecoratedBox(
                    decoration: BoxDecoration(
                      border: Border(
                        top: BorderSide(color: Theme.of(context).dividerColor),
                      ),
                    ),
                    child: bottomNavigation!,
                  ),
              ],
            ),
    );
  }
}

class DemoIndicator extends StatelessWidget {
  const DemoIndicator({super.key});
  @override
  Widget build(BuildContext context) => Tooltip(
    message: context.l.demo,
    child: Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(
        color: context.theme.colors.secondary,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        context.l.demoShort,
        style: TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w600,
          color: context.theme.colors.mutedForeground,
        ),
      ),
    ),
  );
}

class LanguagePicker extends ConsumerWidget {
  const LanguagePicker({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final current = Localizations.localeOf(context).languageCode;
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [
        for (final (code, label) in [
          ('kk', 'Қазақша'),
          ('ru', 'Русский'),
          ('en', 'English'),
        ])
          ChoiceChip(
            label: Text(
              label,
              style: TextStyle(
                fontWeight: current == code ? FontWeight.w600 : FontWeight.w500,
                color: current == code
                    ? context.theme.colors.primaryForeground
                    : context.theme.colors.foreground,
              ),
            ),
            selected: current == code,
            showCheckmark: false,
            onSelected: (_) => ref.read(localeProvider.notifier).select(code),
          ),
      ],
    );
  }
}

class RequestView<T> extends StatelessWidget {
  const RequestView({
    super.key,
    required this.value,
    required this.retry,
    required this.builder,
  });
  final AsyncValue<T> value;
  final VoidCallback retry;
  final Widget Function(T) builder;
  @override
  Widget build(BuildContext context) => value.when(
    skipLoadingOnRefresh: false,
    data: builder,
    loading: () => const Padding(
      padding: EdgeInsets.all(40),
      child: Center(child: FCircularProgress()),
    ),
    error: (error, _) => Padding(
      padding: const EdgeInsets.symmetric(vertical: 16),
      child: Column(
        spacing: 16,
        children: [
          ErrorNotice(error: error),
          FButton(
            builder: fitButtonLabel,
            size: .lg,
            variant: FButtonVariant.outline,
            onPress: retry,
            child: Text(context.l.retry),
          ),
        ],
      ),
    ),
  );
}

String errorMessage(BuildContext context, Object error) {
  if (error is DioException) {
    final data = error.response?.data;
    final detail = data is Map ? data['detail'] : null;
    if ([
      DioExceptionType.connectionError,
      DioExceptionType.connectionTimeout,
      DioExceptionType.receiveTimeout,
      DioExceptionType.sendTimeout,
    ].contains(error.type)) {
      return context.l.offline;
    }
    if (detail == 'Invalid email or password' ||
        (error.response?.statusCode == 401 &&
            error.requestOptions.extra['requiresAuth'] == false)) {
      return context.l.badCredentials;
    }
    if (detail == 'event_cancelled' ||
        detail == 'Cannot check in to a cancelled event') {
      return context.l.eventCancelled;
    }
    if (detail == 'Cannot check in to a suspended event') {
      return context.l.forbidden;
    }
    if (error.response?.statusCode == 400 &&
        [
          'tickets/check-in',
          'tickets/undo-check-in',
        ].contains(error.requestOptions.path)) {
      return context.l.conflict;
    }
    return switch (error.response?.statusCode) {
      401 => context.l.unauthorized,
      403 => context.l.forbidden,
      404 => context.l.notFound,
      409 => context.l.conflict,
      422 =>
        detail is String && detail.trim().isNotEmpty
            ? detail
            : context.l.validationError,
      _ => context.l.serverError,
    };
  }
  // A parse or other non-Dio failure is not a broken saved session.
  return context.l.genericError;
}

class MessageNotice extends StatelessWidget {
  const MessageNotice({
    super.key,
    required this.message,
    this.icon = Icons.error_outline_rounded,
  });
  final String message;
  final IconData icon;
  @override
  Widget build(BuildContext context) => Semantics(
    liveRegion: true,
    child: Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.errorContainer,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            icon,
            color: Theme.of(context).colorScheme.onErrorContainer,
            size: 20,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              message,
              style: TextStyle(
                color: Theme.of(context).colorScheme.onErrorContainer,
              ),
            ),
          ),
        ],
      ),
    ),
  );
}

class ErrorNotice extends StatelessWidget {
  const ErrorNotice({super.key, required this.error});
  final Object error;
  @override
  Widget build(BuildContext context) =>
      MessageNotice(message: errorMessage(context, error));
}

class SurfaceGroup extends StatelessWidget {
  const SurfaceGroup({super.key, required this.child, this.radius = 18});
  final Widget child;
  final double radius;
  @override
  Widget build(BuildContext context) => Material(
    color: context.theme.colors.card,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(radius),
      side: BorderSide(color: context.theme.colors.border),
    ),
    clipBehavior: Clip.antiAlias,
    child: child,
  );
}

String nameInitials(String? fullName, [String? fallback]) {
  final parts = (fullName ?? '')
      .trim()
      .split(RegExp(r'\s+'))
      .where((p) => p.isNotEmpty)
      .toList();
  if (parts.isNotEmpty) {
    return parts.take(2).map((p) => p.characters.first).join().toUpperCase();
  }
  final alt = (fallback ?? '').trim();
  return alt.isNotEmpty ? alt.characters.first.toUpperCase() : '?';
}

class InfoCard extends StatelessWidget {
  const InfoCard({
    super.key,
    this.title,
    this.subtitle,
    required this.child,
    this.onTap,
  });
  final Widget? title, subtitle;
  final Widget child;
  final VoidCallback? onTap;
  @override
  Widget build(BuildContext context) => Material(
    color: context.theme.colors.card,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(18),
      side: BorderSide(color: context.theme.colors.border),
    ),
    clipBehavior: Clip.antiAlias,
    child: InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          spacing: 12,
          children: [
            if (title != null)
              DefaultTextStyle.merge(
                style: Theme.of(context).textTheme.titleLarge,
                child: title!,
              ),
            ?subtitle,
            child,
          ],
        ),
      ),
    ),
  );
}

class StatusTag extends StatelessWidget {
  const StatusTag({super.key, required this.status});
  final String status;
  @override
  Widget build(BuildContext context) {
    final positive = status == 'valid' || status == 'published';
    final used = status == 'checked_in';
    final color = positive
        ? context.theme.colors.primary
        : used
        ? warningColor(context)
        : context.theme.colors.error;
    final icon = positive
        ? Icons.check_circle_outline_rounded
        : used
        ? Icons.history_rounded
        : Icons.block_rounded;
    return Align(
      alignment: AlignmentDirectional.centerStart,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.11),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          spacing: 5,
          children: [
            Icon(icon, size: 13, color: color),
            Flexible(
              child: Text(
                statusLabel(context, status),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: color,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class DetailRow extends StatelessWidget {
  const DetailRow({
    super.key,
    required this.icon,
    required this.title,
    this.subtitle,
  });
  final IconData icon;
  final String title;
  final String? subtitle;
  @override
  Widget build(BuildContext context) => Row(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Padding(
        padding: const EdgeInsets.only(top: 2),
        child: Icon(
          icon,
          size: 20,
          color: context.theme.colors.mutedForeground,
        ),
      ),
      const SizedBox(width: 14),
      Expanded(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          spacing: 3,
          children: [
            Text(title),
            if (subtitle != null)
              Text(subtitle!, style: Theme.of(context).textTheme.bodySmall),
          ],
        ),
      ),
    ],
  );
}

Future<void> openPage(BuildContext context, Widget page) async {
  await Navigator.of(
    context,
  ).push(MaterialPageRoute<void>(builder: (_) => page));
}

Future<T?> appSheet<T>(
  BuildContext context, {
  required String title,
  required Widget child,
}) => showModalBottomSheet<T>(
  context: context,
  useRootNavigator: false,
  isScrollControlled: true,
  useSafeArea: true,
  showDragHandle: true,
  backgroundColor: Theme.of(context).cardColor,
  constraints: BoxConstraints(
    maxWidth: 640,
    maxHeight: MediaQuery.sizeOf(context).height * 0.9,
  ),
  builder: (context) => SingleChildScrollView(
    child: SafeArea(
      top: false,
      child: Padding(
        padding: EdgeInsets.fromLTRB(
          24,
          0,
          24,
          24 + MediaQuery.viewInsetsOf(context).bottom,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          spacing: 20,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    title,
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                ),
                IconButton(
                  tooltip: MaterialLocalizations.of(context).closeButtonTooltip,
                  onPressed: () => Navigator.of(context).maybePop(),
                  icon: const Icon(Icons.close_rounded),
                ),
              ],
            ),
            child,
          ],
        ),
      ),
    ),
  ),
);

Widget fitButtonLabel(
  BuildContext context,
  FButtonStyle style,
  TextStyle textStyle,
  IconThemeData iconStyle,
  FCircularProgressStyle progressStyle,
  Widget? child,
) => Flexible(
  child: DefaultTextStyle.merge(textAlign: TextAlign.center, child: child!),
);
