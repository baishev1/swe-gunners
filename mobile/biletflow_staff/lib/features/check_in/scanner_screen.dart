import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:forui/forui.dart';
import 'package:mobile_scanner/mobile_scanner.dart';

import '../../core/localization/locale_provider.dart';
import '../../core/network/mock_api_adapter.dart';
import '../../core/widgets/app_page.dart';
import '../events/event.dart';
import 'check_in_controller.dart';
import 'ticket_screen.dart';

class ScannerScreen extends ConsumerStatefulWidget {
  const ScannerScreen({super.key, required this.event, this.embedded = false});
  final StaffEvent event;
  final bool embedded;
  @override
  ConsumerState<ScannerScreen> createState() => _ScannerScreenState();
}

class _ScannerScreenState extends ConsumerState<ScannerScreen>
    with WidgetsBindingObserver {
  static final _ticketId = RegExp(
    r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$',
  );
  final _camera = MobileScannerController(
    autoStart: false,
    formats: const [BarcodeFormat.qrCode],
  );
  bool _busy = false, _cameraEnabled = false;
  Object? _error;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    if (!ref.read(useMockApiProvider)) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) _toggleCamera();
      });
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    unawaited(_camera.dispose());
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (!_camera.value.hasCameraPermission || !_cameraEnabled) return;
    if (state == AppLifecycleState.resumed && !_busy) {
      unawaited(_startCamera());
    } else if (state != AppLifecycleState.resumed) {
      unawaited(_stopCamera());
    }
  }

  Future<void> _startCamera() async {
    try {
      await _camera.start();
    } catch (error) {
      if (mounted) setState(() => _error = error);
    }
  }

  Future<void> _stopCamera() async {
    try {
      await _camera.stop();
    } catch (error) {
      if (mounted) setState(() => _error = error);
    }
  }

  Future<void> _toggleCamera() async {
    setState(() {
      _cameraEnabled = !_cameraEnabled;
      _error = null;
    });
    if (_cameraEnabled) {
      await _startCamera();
    } else {
      await _stopCamera();
    }
  }

  Future<void> _verify(String code) async {
    if (_busy) return;
    final value = code.trim();
    final resumeCamera = _cameraEnabled;
    if (resumeCamera) await _stopCamera();
    // A ticket UUID from manual entry resolves through attendee search; all
    // other values are admission QR tokens.
    if (_ticketId.hasMatch(value)) {
      if (!mounted) return;
      await openPage(
        context,
        TicketScreen(event: widget.event, ticketId: value, fromScanner: true),
      );
      if (mounted && resumeCamera) unawaited(_startCamera());
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
      _cameraEnabled = false;
    });
    try {
      final result = await ref
          .read(checkInControllerProvider)
          .verify(widget.event.id, value);
      if (!mounted) return;
      await openPage(
        context,
        TicketScreen(
          event: widget.event,
          verification: result,
          qrToken: value,
          fromScanner: true,
        ),
      );
    } catch (error) {
      if (mounted) setState(() => _error = error);
    } finally {
      if (mounted) {
        setState(() {
          _busy = false;
          _cameraEnabled = resumeCamera;
        });
        if (resumeCamera) unawaited(_startCamera());
      }
    }
  }

  Future<void> _manualEntry() async {
    if (_busy) return;
    final code = await appSheet<String>(
      context,
      title: context.l.manualEntry,
      child: const _ManualCodeForm(),
    );
    if (mounted && code != null) await _verify(code);
  }

  Future<void> _demoEntry() async {
    final code = await appSheet<String>(
      context,
      title: context.l.demoScans,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          for (final (code, label, hint, icon) in [
            (
              'DEMO-VALID',
              context.l.valid,
              'DEMO-VALID',
              Icons.check_circle_outline,
            ),
            ('DEMO-USED', context.l.checked_in, 'DEMO-USED', Icons.history),
            (
              'DEMO-CANCELLED',
              context.l.cancelled,
              'DEMO-CANCELLED',
              Icons.block,
            ),
            ('DEMO-REFUNDED', context.l.refunded, 'DEMO-REFUNDED', Icons.undo),
            (
              'DEMO-OTHER',
              context.l.wrong_event,
              'DEMO-OTHER',
              Icons.event_busy_outlined,
            ),
            (
              'https://biletflow.demo/events/detail?event_id=demo&promo=spring',
              context.l.campaign_qr,
              'promo=spring',
              Icons.campaign_outlined,
            ),
            ('TAMPERED', context.l.invalid, 'TAMPERED', Icons.error_outline),
            (
              'DEMO-GENERAL',
              context.l.generalAdmission,
              'DEMO-GENERAL',
              Icons.confirmation_number_outlined,
            ),
          ])
            ListTile(
              contentPadding: EdgeInsets.zero,
              minVerticalPadding: 10,
              leading: Icon(icon),
              title: Text(label),
              subtitle: Text(
                hint,
                style: Theme.of(context).textTheme.bodySmall,
              ),
              trailing: const Icon(Icons.chevron_right_rounded),
              onTap: () => Navigator.pop(context, code),
            ),
        ],
      ),
    );
    if (mounted && code != null) await _verify(code);
  }

  @override
  Widget build(BuildContext context) {
    final children = <Widget>[
      Text(context.l.scanTab, style: Theme.of(context).textTheme.headlineLarge),
      Column(
        spacing: 8,
        children: [
          Text(
            _busy ? context.l.checkingTicket : context.l.readyToScan,
            style: Theme.of(context).textTheme.titleLarge,
            textAlign: TextAlign.center,
          ),
          Text(
            context.l.scanGuide,
            textAlign: TextAlign.center,
            style: TextStyle(color: context.theme.colors.mutedForeground),
          ),
        ],
      ),
      LayoutBuilder(
        builder: (context, constraints) {
          final height = (MediaQuery.sizeOf(context).height * 0.34).clamp(
            220.0,
            340.0,
          );
          return ClipRRect(
            borderRadius: BorderRadius.circular(24),
            child: SizedBox(
              height: height,
              child: Stack(
                fit: StackFit.expand,
                children: [
                  if (_cameraEnabled)
                    MobileScanner(
                      controller: _camera,
                      useAppLifecycleState: false,
                      onDetect: (capture) {
                        final code = capture.barcodes.firstOrNull?.rawValue;
                        if (code != null) unawaited(_verify(code));
                      },
                      onDetectError: (error, _) {
                        if (mounted) setState(() => _error = error);
                      },
                      errorBuilder: (context, error) => ColoredBox(
                        color: context.theme.colors.muted,
                        child: Center(
                          child: Padding(
                            padding: const EdgeInsets.all(24),
                            child: Text(
                              context.l.cameraError,
                              textAlign: TextAlign.center,
                            ),
                          ),
                        ),
                      ),
                    )
                  else
                    ColoredBox(color: context.theme.colors.muted),
                  IgnorePointer(
                    child: Center(
                      child: Container(
                        width: constraints.maxWidth * 0.62,
                        height: height * 0.68,
                        decoration: BoxDecoration(
                          border: Border.all(
                            color: _cameraEnabled
                                ? Colors.white.withValues(alpha: 0.85)
                                : context.theme.colors.primary.withValues(
                                    alpha: 0.45,
                                  ),
                            width: 2,
                          ),
                          borderRadius: BorderRadius.circular(18),
                        ),
                      ),
                    ),
                  ),
                  if (_busy)
                    const Center(child: FCircularProgress())
                  else if (!_cameraEnabled)
                    Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        spacing: 10,
                        children: [
                          IconButton.filled(
                            tooltip: context.l.openCamera,
                            style: IconButton.styleFrom(
                              minimumSize: const Size(64, 64),
                            ),
                            onPressed: _toggleCamera,
                            icon: const Icon(Icons.videocam_outlined, size: 28),
                          ),
                          Text(
                            context.l.openCamera,
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                        ],
                      ),
                    ),
                  if (_cameraEnabled)
                    Positioned(
                      bottom: 12,
                      right: 12,
                      child: ValueListenableBuilder<MobileScannerState>(
                        valueListenable: _camera,
                        builder: (context, state, _) {
                          final torchOn = state.torchState == TorchState.on;
                          return IconButton.filled(
                            tooltip: context.l.torch,
                            style: IconButton.styleFrom(
                              backgroundColor: torchOn
                                  ? context.theme.colors.primary
                                  : Colors.black.withValues(alpha: 0.55),
                              foregroundColor: torchOn
                                  ? context.theme.colors.primaryForeground
                                  : Colors.white,
                            ),
                            onPressed: _busy
                                ? null
                                : () async {
                                    try {
                                      await _camera.toggleTorch();
                                    } catch (error) {
                                      if (mounted) {
                                        setState(() => _error = error);
                                      }
                                    }
                                  },
                            icon: Icon(
                              torchOn
                                  ? Icons.flashlight_on_rounded
                                  : Icons.flashlight_off_outlined,
                            ),
                          );
                        },
                      ),
                    ),
                  if (_cameraEnabled)
                    Positioned(
                      top: 12,
                      right: 12,
                      child: IconButton.filled(
                        tooltip: context.l.closeCamera,
                        style: IconButton.styleFrom(
                          backgroundColor: Colors.black.withValues(alpha: 0.55),
                          foregroundColor: Colors.white,
                        ),
                        onPressed: _busy ? null : _toggleCamera,
                        icon: const Icon(Icons.close_rounded),
                      ),
                    ),
                ],
              ),
            ),
          );
        },
      ),
      if (_error is MobileScannerException)
        MessageNotice(
          message: context.l.cameraError,
          icon: Icons.videocam_off_outlined,
        )
      else if (_error != null)
        ErrorNotice(error: _error!),
      FButton(
        builder: fitButtonLabel,
        size: .lg,
        variant: FButtonVariant.outline,
        prefix: const Icon(Icons.keyboard_outlined),
        onPress: _busy ? null : _manualEntry,
        child: Text(context.l.manualEntry),
      ),
      if (ref.watch(useMockApiProvider))
        Center(
          child: TextButton.icon(
            onPressed: _busy ? null : _demoEntry,
            icon: const Icon(Icons.science_outlined, size: 18),
            label: Text(context.l.demoChoose),
          ),
        ),
    ];
    if (widget.embedded) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        spacing: 22,
        children: children,
      );
    }
    return AppPage(title: widget.event.title, children: children);
  }
}

class _ManualCodeForm extends StatefulWidget {
  const _ManualCodeForm();
  @override
  State<_ManualCodeForm> createState() => _ManualCodeFormState();
}

class _ManualCodeFormState extends State<_ManualCodeForm> {
  final _code = TextEditingController();
  bool _submitted = false;

  @override
  void initState() {
    super.initState();
    _code.addListener(_onChanged);
  }

  void _onChanged() {
    if (_submitted && _code.text.trim().isNotEmpty) {
      setState(() => _submitted = false);
    }
  }

  @override
  void dispose() {
    _code.removeListener(_onChanged);
    _code.dispose();
    super.dispose();
  }

  void _submit() {
    if (_code.text.trim().isEmpty) {
      setState(() => _submitted = true);
      return;
    }
    Navigator.pop(context, _code.text.trim());
  }

  @override
  Widget build(BuildContext context) => Column(
    mainAxisSize: MainAxisSize.min,
    crossAxisAlignment: CrossAxisAlignment.stretch,
    spacing: 20,
    children: [
      FTextField(
        control: FTextFieldControl.managed(controller: _code),
        autofocus: true,
        label: Text(context.l.manualCode),
        textInputAction: TextInputAction.done,
        onSubmit: (_) => _submit(),
        error: _submitted && _code.text.trim().isEmpty
            ? Text(context.l.requiredField)
            : null,
      ),
      Text(
        context.l.manualCodeHint,
        style: Theme.of(context).textTheme.bodySmall,
      ),
      FButton(
        builder: fitButtonLabel,
        size: .lg,
        onPress: _submit,
        child: Text(context.l.verify),
      ),
    ],
  );
}
