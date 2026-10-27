import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:forui/forui.dart';

import '../../core/localization/locale_provider.dart';
import '../../core/network/api_client.dart';
import '../../core/network/mock_api_adapter.dart';
import '../../core/network/mock_fixtures.dart';
import '../../core/widgets/app_page.dart';
import 'session_controller.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key, this.reset = false});
  final bool reset;
  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _email = TextEditingController(text: useMockApi ? demoEmail : '');
  final _password = TextEditingController(text: useMockApi ? demoPassword : '');
  bool _busy = false, _obscure = true, _submitted = false, _sent = false;
  Object? _error;
  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() {
      _submitted = true;
      _error = null;
    });
    if (!_email.text.contains(RegExp(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')) ||
        (!widget.reset && _password.text.isEmpty)) {
      return;
    }
    setState(() => _busy = true);
    try {
      final response = await ref
          .read(dioProvider)
          .post<Map<String, dynamic>>(
            widget.reset ? 'auth/forgot-password' : 'auth/login',
            data: {
              'email': _email.text.trim(),
              if (!widget.reset) 'password': _password.text,
            },
            options: Options(extra: {'requiresAuth': false}),
          );
      if (!mounted) return;
      if (widget.reset) {
        setState(() => _sent = true);
      } else {
        await ref
            .read(sessionProvider.notifier)
            .saveToken(response.data!['access_token'] as String);
      }
    } catch (error) {
      if (mounted) setState(() => _error = error);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => AppPage(
    title: 'Biletflow',
    back: widget.reset,
    actions: [
      IconButton(
        tooltip: context.l.language,
        onPressed: () => appSheet<void>(
          context,
          title: context.l.language,
          child: const LanguagePicker(),
        ),
        icon: const Icon(Icons.language_rounded),
      ),
    ],
    children: [
      const SizedBox(height: 20),
      Align(
        alignment: AlignmentDirectional.centerStart,
        child: Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: context.theme.colors.secondary,
            borderRadius: BorderRadius.circular(16),
          ),
          child: Icon(
            widget.reset
                ? Icons.lock_reset_rounded
                : Icons.confirmation_number_outlined,
            size: 30,
            color: context.theme.colors.primary,
          ),
        ),
      ),
      Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        spacing: 12,
        children: [
          Text(
            widget.reset ? context.l.resetPassword : context.l.welcomeTitle,
            style: Theme.of(context).textTheme.headlineLarge,
          ),
          Text(
            widget.reset ? context.l.resetHint : context.l.welcomeBody,
            style: TextStyle(color: context.theme.colors.mutedForeground),
          ),
        ],
      ),
      const SizedBox(height: 4),
      if (_sent)
        InfoCard(
          child: DetailRow(
            icon: Icons.mark_email_read_outlined,
            title: context.l.resetSent,
          ),
        )
      else ...[
        AutofillGroup(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            spacing: 20,
            children: [
              FTextField.email(
                control: FTextFieldControl.managed(controller: _email),
                label: Text(context.l.email),
                enabled: !_busy,
                autofillHints: const [AutofillHints.username],
                error:
                    _submitted &&
                        !_email.text.contains(
                          RegExp(r'^[^\s@]+@[^\s@]+\.[^\s@]+$'),
                        )
                    ? Text(context.l.invalidEmail)
                    : null,
              ),
              if (!widget.reset)
                FTextField(
                  control: FTextFieldControl.managed(controller: _password),
                  label: Text(context.l.password),
                  obscureText: _obscure,
                  enabled: !_busy,
                  autocorrect: false,
                  enableSuggestions: false,
                  autofillHints: const [AutofillHints.password],
                  textInputAction: TextInputAction.done,
                  onSubmit: (_) => _submit(),
                  error: _submitted && _password.text.isEmpty
                      ? Text(context.l.requiredField)
                      : null,
                  suffixBuilder: (_, _, _) => IconButton(
                    tooltip: _obscure
                        ? context.l.showPassword
                        : context.l.hidePassword,
                    onPressed: () => setState(() => _obscure = !_obscure),
                    icon: Icon(
                      _obscure
                          ? Icons.visibility_outlined
                          : Icons.visibility_off_outlined,
                      size: 20,
                    ),
                  ),
                ),
            ],
          ),
        ),
        if (!widget.reset)
          Align(
            alignment: AlignmentDirectional.centerEnd,
            child: TextButton(
              onPressed: _busy
                  ? null
                  : () => openPage(context, const LoginScreen(reset: true)),
              child: Text(context.l.forgotPassword),
            ),
          ),
        if (_error != null) ErrorNotice(error: _error!),
        FButton(
          builder: fitButtonLabel,
          size: .lg,
          onPress: _busy ? null : _submit,
          child: _busy
              ? const FCircularProgress()
              : Text(widget.reset ? context.l.sendReset : context.l.signIn),
        ),
      ],
      if (useMockApi && !widget.reset)
        Text(
          context.l.demoLoginHint,
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.bodySmall,
        ),
    ],
  );
}
