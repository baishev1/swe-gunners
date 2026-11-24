import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:forui/forui.dart';

import '../../core/localization/locale_provider.dart';
import '../../core/theme/app_theme.dart';
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
    this.attendee,
    this.fromScanner = false,
  });
  final StaffEvent event;
  final TicketVerification? verification;
  final String? qrToken;
  final String? ticketId;
  final AdmissionTicket? attendee;
  final bool fromScanner;
  @override
  ConsumerState<TicketScreen> createState() => _TicketScreenState();
}

class _TicketScreenState extends ConsumerState<TicketScreen> {
  AdmissionTicket? _ticket;
  String _result = '';
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
      final attendee = widget.attendee;
      if (attendee != null) {
        _ticket = attendee;
        _result = attendee.status;
        _valid = attendee.status == 'valid';
      } else {
        _load();
      }
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
      final ticketId = widget.ticketId ?? _ticket?.id ?? widget.attendee?.id;
      if (ticketId == null) return;
      // The backend exposes no check-in detail route; resolve the row through
      // the assigned-event attendee search instead.
      final row = await ref
          .read(checkInControllerProvider)
          .findAttendee(widget.event.id, ticketId);
      if (!mounted) return;
      setState(() {
        _ticket = row;
        _result = row?.status ?? 'not_found';
        _valid = row?.status == 'valid';
        _success = null;
      });
    } catch (error) {
      if (mounted) setState(() => _error = error);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _refreshAttendee() async {
    final ticketId = _ticket?.id;
    if (ticketId == null) return;
    try {
      final row = await ref
          .read(checkInControllerProvider)
          .findAttendee(widget.event.id, ticketId);
      if (!mounted) return;
      setState(() {
        _ticket = row;
        _result = row?.status ?? 'not_found';
        _valid = row?.status == 'valid';
      });
    } catch (_) {
      // Keep the authoritative change response; the refresh can retry.
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
      HapticFeedback.mediumImpact();
      setState(() {
        _ticket = result;
        _result = result.status;
        _valid = _result == 'valid';
        _success = undo ? 'undo' : 'admit';
      });
      if (widget.verification == null) await _refreshAttendee();
    } catch (error) {
      HapticFeedback.heavyImpact();
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
    final account = _result == 'checked_in'
        ? ref.watch(accountProvider).asData?.value
        : null;
    final canUndo =
        widget.event.canUndoCheckIn ||
        account?['id'] == widget.event.organizerId ||
        account?['role'] == 'platform_admin';
    final allowed = ['valid', 'checked_in'].contains(_result);
    final successful = _success == 'admit';
    final alreadyUsed = _result == 'checked_in' && !successful;
    final color = successful || _result == 'valid'
        ? context.theme.colors.primary
        : alreadyUsed
        ? warningColor(context)
        : context.theme.colors.error;
    final statusIcon = successful || _result == 'valid'
        ? (_success == 'undo' ? Icons.undo_rounded : Icons.check_rounded)
        : alreadyUsed
        ? Icons.history_rounded
        : _result == 'not_found'
        ? Icons.search_off_rounded
        : Icons.block_rounded;
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
    final showResult =
        widget.verification != null || ticket != null || _result == 'not_found';
    final loadFailed =
        _error != null && ticket == null && widget.verification == null;
    final canRefresh =
        ticket != null ||
        widget.ticketId != null ||
        widget.attendee != null ||
        widget.qrToken != null;
    final canPop = Navigator.of(context).canPop();
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
      } else if (widget.verification != null || widget.fromScanner) {
        primary = FButton(
          builder: fitButtonLabel,
          size: .lg,
          onPress: _busy ? null : () => Navigator.of(context).maybePop(),
          prefix: const Icon(Icons.qr_code_scanner_rounded),
          child: Text(context.l.scanNext),
        );
      } else if (canPop) {
        primary = FButton(
          builder: fitButtonLabel,
          size: .lg,
          variant: FButtonVariant.outline,
          onPress: _busy ? null : () => Navigator.of(context).maybePop(),
          prefix: const Icon(Icons.arrow_back_rounded),
          child: Text(context.l.back),
        );
      }
    }
    return AppPage(
      title: widget.verification == null
          ? context.l.ticket
          : context.l.verification,
      onRefresh: canRefresh && !_busy ? _load : null,
      actions: [
        if (canRefresh)
          IconButton(
            tooltip: context.l.refresh,
            onPressed: _busy || _loading ? null : _load,
            icon: const Icon(Icons.refresh_rounded),
          ),
      ],
      footer: primary,
      children: [
        if (_loading && ticket == null)
          const Padding(
            padding: EdgeInsets.all(48),
            child: Center(child: FCircularProgress()),
          )
        else if (loadFailed) ...[
          ErrorNotice(error: _error!),
          FButton(
            builder: fitButtonLabel,
            size: .lg,
            variant: FButtonVariant.outline,
            onPress: _load,
            child: Text(context.l.retry),
          ),
        ] else if (showResult) ...[
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
                    color: color.withValues(alpha: 0.12),
                  ),
                  child: Icon(statusIcon, size: 44, color: color),
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
          if (_error != null) ...[
            ErrorNotice(error: _error!),
            if (canRefresh)
              FButton(
                builder: fitButtonLabel,
                size: .lg,
                variant: FButtonVariant.outline,
                prefix: const Icon(Icons.refresh_rounded),
                onPress: _busy || _loading ? null : _load,
                child: Text(context.l.refresh),
              ),
          ],
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
                          nameInitials(ticket.name, ticket.email),
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
                  DetailRow(
                    icon: Icons.event_seat_outlined,
                    title:
                        ticket.assignedSeatLabel ?? context.l.generalAdmission,
                    subtitle: context.l.seat,
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
              shape: const Border(),
              collapsedShape: const Border(),
              expandedAlignment: AlignmentDirectional.centerStart,
              childrenPadding: const EdgeInsets.only(bottom: 12),
              title: Text(
                context.l.ticket,
                style: Theme.of(context).textTheme.bodySmall,
              ),
              children: [
                Row(
                  children: [
                    Expanded(
                      child: SelectableText(
                        ticket.id,
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ),
                    IconButton(
                      tooltip: MaterialLocalizations.of(
                        context,
                      ).copyButtonLabel,
                      onPressed: () {
                        Clipboard.setData(ClipboardData(text: ticket.id));
                        HapticFeedback.selectionClick();
                      },
                      icon: const Icon(Icons.copy_rounded, size: 18),
                    ),
                  ],
                ),
              ],
            ),
        ],
      ],
    );
  }
}
