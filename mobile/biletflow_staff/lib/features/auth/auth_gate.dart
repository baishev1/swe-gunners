import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:forui/forui.dart';

import '../../core/localization/locale_provider.dart';
import '../../core/widgets/app_page.dart';
import '../events/events_screen.dart';
import 'login_screen.dart';
import 'session_controller.dart';

class AuthGate extends ConsumerWidget {
  const AuthGate({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) => ref
      .watch(sessionProvider)
      .when(
        loading: () =>
            const FScaffold(child: Center(child: FCircularProgress())),
        error: (_, _) => AppPage(
          title: context.l.appName,
          back: false,
          children: [
            MessageNotice(message: context.l.storageError),
            FButton(
              builder: fitButtonLabel,
              size: .lg,
              onPress: () async {
                final session = ref.read(sessionProvider.notifier);
                if (session.mustClear) {
                  try {
                    await session.logout();
                  } catch (_) {
                    /* Keep showing the storage error. */
                  }
                } else {
                  ref.invalidate(sessionProvider);
                }
              },
              child: Text(context.l.retry),
            ),
          ],
        ),
        data: (token) =>
            _SessionNavigator(key: ValueKey(token), signedIn: token != null),
      );
}

class _SessionNavigator extends StatefulWidget {
  const _SessionNavigator({super.key, required this.signedIn});
  final bool signedIn;
  @override
  State<_SessionNavigator> createState() => _SessionNavigatorState();
}

class _SessionNavigatorState extends State<_SessionNavigator> {
  final _navigator = GlobalKey<NavigatorState>();
  bool _canPop = false;

  void _syncCanPop() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      final canPop = _navigator.currentState?.canPop() ?? false;
      if (canPop != _canPop) setState(() => _canPop = canPop);
    });
  }

  @override
  Widget build(BuildContext context) => NavigatorPopHandler<void>(
    enabled: _canPop,
    onPopWithResult: (_) => _navigator.currentState?.maybePop(),
    child: Navigator(
      key: _navigator,
      observers: [_CanPopObserver(_syncCanPop)],
      onGenerateRoute: (_) => MaterialPageRoute<void>(
        builder: (_) =>
            widget.signedIn ? const EventsScreen() : const LoginScreen(),
      ),
    ),
  );
}

class _CanPopObserver extends NavigatorObserver {
  _CanPopObserver(this.onChange);
  final VoidCallback onChange;
  @override
  void didPush(Route<dynamic> route, Route<dynamic>? previousRoute) =>
      onChange();
  @override
  void didPop(Route<dynamic> route, Route<dynamic>? previousRoute) =>
      onChange();
  @override
  void didRemove(Route<dynamic> route, Route<dynamic>? previousRoute) =>
      onChange();
  @override
  void didReplace({Route<dynamic>? newRoute, Route<dynamic>? oldRoute}) =>
      onChange();
}
