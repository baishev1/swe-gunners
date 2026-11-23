import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:forui/forui.dart';

import '../../core/localization/locale_provider.dart';
import '../../core/network/api_client.dart';
import '../../core/network/mock_api_adapter.dart';
import '../../core/widgets/app_page.dart';
import '../events/event.dart';
import '../events/event_providers.dart';
import 'check_in_controller.dart';
import 'ticket.dart';

class TicketScreen extends ConsumerStatefulWidget {
  const TicketScreen({
    super.key,
    required this.event,
    this.verification,
    this.qrToken,
    this.ticketId,
  });
  final StaffEvent event;
  final TicketVerification? verification;
  final String? qrToken;
  final String? ticketId;
  @override
  ConsumerState<TicketScreen> createState() => _TicketScreenState();
}

class _TicketScreenState extends ConsumerState<TicketScreen> {
  AdmissionTicket? _ticket;
  String _result = 'invalid';
  bool _valid = false;
  String? _success;
  bool _busy = false, _loading = false;
  Object? _error;

  @override
  void initState() {
    super.initState();
    final verification = widget.verification;
    if (verification != null) {
      _applyVerification(verification);
    } else {
      _load();
    }
  }

  void _applyVerification(TicketVerification verification) {
    _result = verification.status;
    _valid = verification.valid;
    _ticket = verification.ticket;
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final qrToken = widget.qrToken;
      if (qrToken != null) {
        final result = await ref
            .read(checkInControllerProvider)
            .verify(widget.event.id, qrToken);
        if (!mounted) return;
        setState(() {
          _applyVerification(result);
          _success = null;
        });
        return;
      }
      final response = await ref
          .read(dioProvider)
          .get<Map<String, dynamic>>(
            'checkin/tickets/detail',
            queryParameters: {
              'event_id': widget.event.id,
              'ticket_id': widget.ticketId ?? _ticket?.id,
            },
          );
      if (!mounted) return;
      setState(() {
        _ticket = AdmissionTicket.fromJson(response.data!);
        _result = _ticket!.status;
        _valid = _result == 'valid';
        _success = null;
      });
    } catch (error) {
      if (mounted) setState(() => _error = error);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _change({required bool undo}) async {
    if (_busy) return;
    setState(() => _busy = true);
    if (undo) {
      final confirm = await showDialog<bool>(
        context: context,
        useRootNavigator: false,
        builder: (context) => AlertDialog(
          title: Text(context.l.undoTitle),
          content: Text(context.l.undoHint),
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
      if (!mounted) return;
      if (confirm != true) {
        setState(() => _busy = false);
        return;
      }
    }
    setState(() => _error = null);
    try {
      final result = await ref
          .read(checkInControllerProvider)
          .change(widget.event.id, _ticket!.id, undo: undo);
      if (!mounted) return;
      setState(() {
        _ticket = result;
        _result = result.status;
        _valid = _result == 'valid';
        _success = undo ? 'undo' : 'admit';
      });
    } catch (error) {
      if (mounted) {
        setState(() {
          _error = error;
          _success = null;
        });
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final ticket = _ticket;
    final account = !useMockApi && _result == 'checked_in'
        ? ref.watch(accountProvider).asData?.value
        : null;
    final canUndo = useMockApi
        ? ticket?.canUndo == true
        : widget.event.canUndoCheckIn ||
              account?['id'] == widget.event.organizerId ||
              account?['role'] == 'platform_admin';
    final allowed =
        !widget.event.cancelled && ['valid', 'checked_in'].contains(_result);
    final successful = _success == 'admit';
    final color = allowed
        ? context.theme.colors.primary
        : context.theme.colors.error;
    final headline = successful
        ? context.l.admitted
        : _success == 'undo'
        ? context.l.undoDone
        : statusLabel(context, _result);
    final hint = successful
        ? context.l.admittedHint
        : _result == 'valid'
        ? context.l.admissionHint
        : _result == 'checked_in'
        ? context.l.usedHint
        : context.l.blockedHint;
    Widget? primary;
    if (!_loading) {
      if (ticket != null &&
          allowed &&
          _valid &&
          ticket.status == 'valid' &&
          _error == null) {
        primary = FButton(
          builder: fitButtonLabel,
          size: .lg,
          onPress: _busy ? null : () => _change(undo: false),
          prefix: const Icon(Icons.check_rounded),
          child: _busy ? const FCircularProgress() : Text(context.l.checkIn),
        );
      } else if (widget.verification != null) {
        primary = FButton(
          builder: fitButtonLabel,
          size: .lg,
          onPress: _busy ? null : () => Navigator.pop(context),
          prefix: const Icon(Icons.qr_code_scanner_rounded),
          child: Text(context.l.scanNext),
        );
      }
    }
    return AppPage(
      title: widget.verification == null
          ? context.l.ticket
          : context.l.verification,
      actions: [
        if (ticket != null || widget.ticketId != null)
          IconButton(
            tooltip: context.l.refresh,
            onPressed: _busy || _loading ? null : _load,
            icon: const Icon(Icons.refresh_rounded),
          ),
      ],
      footer: primary,
      children: [
        if (_loading)
          const Padding(
            padding: EdgeInsets.all(48),
            child: Center(child: FCircularProgress()),
          )
        else ...[
          Semantics(
            liveRegion: true,
            child: Column(
              spacing: 16,
              children: [
                const SizedBox(height: 8),
                Container(
                  width: 88,
                  height: 88,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: color.withValues(alpha: 0.10),
                  ),
                  child: Icon(
                    successful || _result == 'valid'
                        ? Icons.check_rounded
                        : _result == 'checked_in'
                        ? Icons.history_rounded
                        : Icons.block_rounded,
                    size: 44,
                    color: color,
                  ),
                ),
                Text(
                  headline,
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.headlineMedium,
                ),
                Text(
                  hint,
                  textAlign: TextAlign.center,
                  style: TextStyle(color: context.theme.colors.mutedForeground),
                ),
                const SizedBox(height: 4),
              ],
            ),
          ),
          if (_error != null) ErrorNotice(error: _error!),
          if (ticket != null)
            InfoCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                spacing: 20,
                children: [
                  Row(
                    children: [
                      CircleAvatar(
                        radius: 24,
                        backgroundColor: context.theme.colors.secondary,
                        foregroundColor: context.theme.colors.primary,
                        child: Text(
                          ticket.name
                              .trim()
                              .split(' ')
                              .where((s) => s.isNotEmpty)
                              .take(2)
                              .map((s) => s.characters.first)
                              .join(),
                          style: const TextStyle(fontWeight: FontWeight.w600),
                        ),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          spacing: 3,
                          children: [
                            Text(
                              ticket.name,
                              style: Theme.of(context).textTheme.titleLarge,
                            ),
                            Text(
                              ticket.email,
                              style: Theme.of(context).textTheme.bodySmall,
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  Divider(height: 1, color: context.theme.colors.border),
                  DetailRow(
                    icon: Icons.confirmation_number_outlined,
                    title: ticket.type,
                    subtitle: context.l.ticketType,
                  ),
                  if (useMockApi || ticket.seat != null)
                    DetailRow(
                      icon: Icons.event_seat_outlined,
                      title: ticket.seat == null
                          ? context.l.generalAdmission
                          : '${ticket.section} / ${ticket.row} / ${ticket.seat}',
                      subtitle: ticket.seat == null ? null : context.l.seat,
                    ),
                  if (ticket.checkedInAt != null)
                    DetailRow(
                      icon: Icons.schedule_rounded,
                      title: eventDate(
                        context,
                        ticket.checkedInAt!,
                        widget.event.timezone,
                      ),
                      subtitle: context.l.checkInTime,
                    ),
                ],
              ),
            ),
          if (widget.event.cancelled) Text(context.l.eventCancelled),
          if (ticket != null && allowed && ticket.status == 'checked_in')
            if (canUndo)
              Center(
                child: TextButton.icon(
                  onPressed: _busy ? null : () => _change(undo: true),
                  icon: const Icon(Icons.undo_rounded, size: 18),
                  label: Text(context.l.undo),
                ),
              )
            else
              Text(
                context.l.permissionDenied,
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodySmall,
              ),
          if (ticket != null)
            ExpansionTile(
              tilePadding: EdgeInsets.zero,
              title: Text(
                context.l.ticket,
                style: Theme.of(context).textTheme.bodySmall,
              ),
              children: [
                SelectableText(
                  ticket.id,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          if (_error != null && ticket == null && widget.ticketId != null)
            FButton(
              builder: fitButtonLabel,
              size: .lg,
              variant: FButtonVariant.outline,
              onPress: _load,
              child: Text(context.l.retry),
            ),
        ],
      ],
    );
  }
}
