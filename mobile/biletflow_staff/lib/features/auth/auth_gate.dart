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
          children: [
            Text(context.l.storageError),
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
  @override
  Widget build(BuildContext context) => NavigatorPopHandler<void>(
    onPopWithResult: (_) => _navigator.currentState!.pop(),
    child: Navigator(
      key: _navigator,
      onGenerateRoute: (_) => MaterialPageRoute<void>(
        builder: (_) =>
            widget.signedIn ? const EventsScreen() : const LoginScreen(),
      ),
    ),
  );
}
