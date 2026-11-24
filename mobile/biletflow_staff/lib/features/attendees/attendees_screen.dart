import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:forui/forui.dart';

import '../../core/localization/locale_provider.dart';
import '../../core/network/api_client.dart';
import '../../core/widgets/app_page.dart';
import '../check_in/ticket.dart';
import '../check_in/ticket_screen.dart';
import '../events/event.dart';

const _pageSize = 20;

class AttendeesScreen extends ConsumerStatefulWidget {
  const AttendeesScreen({
    super.key,
    required this.event,
    this.embedded = false,
  });
  final StaffEvent event;
  final bool embedded;
  @override
  ConsumerState<AttendeesScreen> createState() => AttendeesScreenState();
}

class AttendeesScreenState extends ConsumerState<AttendeesScreen> {
  final _query = TextEditingController();
  final List<AdmissionTicket> _tickets = [];
  Timer? _debounce;
  int _generation = 0;
  bool _busy = false, _loadingMore = false, _hasMore = false;
  Object? _error;
  String _activeQuery = '';

  Future<void> refresh() => _search();

  @override
  void initState() {
    super.initState();
    _query.addListener(_onQuery);
    _search();
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _query.removeListener(_onQuery);
    _query.dispose();
    super.dispose();
  }

  void _onQuery() {
    final trimmed = _query.text.trim();
    if (trimmed == _activeQuery && _debounce == null) return;
    _debounce?.cancel();
    // Invalidate older responses immediately, before the debounce finishes.
    _generation++;
    setState(() {
      _busy = true;
      _loadingMore = false;
      _error = null;
    });
    _debounce = Timer(const Duration(milliseconds: 300), () => _search());
  }

  Future<void> _search({bool more = false}) async {
    if (more && (_busy || _loadingMore || !_hasMore)) return;
    _debounce?.cancel();
    _debounce = null;
    final generation = ++_generation;
    if (!more) _activeQuery = _query.text.trim();
    setState(() {
      _busy = !more;
      _loadingMore = more;
      _error = null;
      if (!more) _tickets.clear();
    });
    try {
      final response = await ref
          .read(dioProvider)
          .get<List<dynamic>>(
            'checkin/attendees',
            queryParameters: {
              'event_id': widget.event.id,
              'q': _activeQuery,
              'limit': _pageSize,
              'offset': more ? _tickets.length : 0,
            },
          );
      if (!mounted || generation != _generation) return;
      final page = response.data ?? const <dynamic>[];
      setState(() {
        _tickets.addAll(
          page.map(
            (e) => AdmissionTicket.fromAttendee(e as Map<String, dynamic>),
          ),
        );
        // The backend returns a bare list: a short page means the end.
        _hasMore = page.length == _pageSize;
      });
    } catch (error) {
      if (mounted && generation == _generation) setState(() => _error = error);
    } finally {
      if (mounted && generation == _generation) {
        setState(() {
          _busy = false;
          _loadingMore = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final children = <Widget>[
      Text(
        context.l.guestsTab,
        style: Theme.of(context).textTheme.headlineLarge,
      ),
      FTextField(
        control: FTextFieldControl.managed(controller: _query),
        hint: context.l.searchHint,
        textInputAction: TextInputAction.search,
        prefixBuilder: (_, _, _) => const Padding(
          padding: EdgeInsets.only(left: 14),
          child: Icon(Icons.search_rounded, size: 20),
        ),
        suffixBuilder: (_, _, _) => ValueListenableBuilder<TextEditingValue>(
          valueListenable: _query,
          builder: (context, value, _) => value.text.isEmpty
              ? const SizedBox.shrink()
              : IconButton(
                  tooltip: context.l.clearSearch,
                  onPressed: () {
                    _query.clear();
                    _search();
                  },
                  icon: const Icon(Icons.close_rounded, size: 18),
                ),
        ),
        onSubmit: (_) => _search(),
      ),
      if (_busy && _tickets.isEmpty)
        const Padding(
          padding: EdgeInsets.all(24),
          child: Center(child: FCircularProgress()),
        ),
      if (!_busy && _error == null && _tickets.isEmpty)
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 24),
          child: Column(
            spacing: 12,
            children: [
              Icon(
                Icons.search_off_rounded,
                size: 44,
                color: context.theme.colors.mutedForeground,
              ),
              Text(
                context.l.noResults,
                style: Theme.of(context).textTheme.titleMedium,
              ),
              Text(
                context.l.noGuestsHint,
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ),
        ),
      if (_tickets.isNotEmpty)
        SurfaceGroup(
          child: Column(
            children: [
              for (var i = 0; i < _tickets.length; i++) ...[
                if (i > 0)
                  Divider(
                    height: 1,
                    indent: 20,
                    endIndent: 20,
                    color: context.theme.colors.border,
                  ),
                _GuestRow(
                  ticket: _tickets[i],
                  onTap: () async {
                    await openPage(
                      context,
                      TicketScreen(event: widget.event, attendee: _tickets[i]),
                    );
                    if (mounted) await _search();
                  },
                ),
              ],
            ],
          ),
        ),
      if (_error != null) ...[
        ErrorNotice(error: _error!),
        FButton(
          builder: fitButtonLabel,
          size: .lg,
          variant: FButtonVariant.outline,
          onPress: () => _search(more: _tickets.isNotEmpty),
          child: Text(context.l.retry),
        ),
      ],
      if (_hasMore && _error == null && !_busy)
        FButton(
          builder: fitButtonLabel,
          size: .lg,
          variant: FButtonVariant.outline,
          onPress: _loadingMore ? null : () => _search(more: true),
          child: _loadingMore
              ? const FCircularProgress()
              : Text(context.l.loadMore),
        ),
    ];
    if (widget.embedded) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        spacing: 20,
        children: children,
      );
    }
    return AppPage(
      title: context.l.attendees,
      onRefresh: () => _search(),
      children: children,
    );
  }
}

class _GuestRow extends StatelessWidget {
  const _GuestRow({required this.ticket, required this.onTap});
  final AdmissionTicket ticket;
  final VoidCallback onTap;
  @override
  Widget build(BuildContext context) => InkWell(
    onTap: onTap,
    child: Padding(
      padding: const EdgeInsets.all(18),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          CircleAvatar(
            radius: 20,
            backgroundColor: context.theme.colors.secondary,
            foregroundColor: context.theme.colors.primary,
            child: Text(
              nameInitials(ticket.name, ticket.email),
              style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              spacing: 5,
              children: [
                Text(
                  ticket.name,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                Text(
                  ticket.assignedSeatLabel != null
                      ? '${ticket.type} · ${ticket.assignedSeatLabel}'
                      : ticket.type,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
                Text(
                  ticket.email,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
                const SizedBox(height: 2),
                StatusTag(status: ticket.status),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.only(top: 8),
            child: Icon(
              Icons.chevron_right_rounded,
              size: 20,
              color: context.theme.colors.mutedForeground,
            ),
          ),
        ],
      ),
    ),
  );
}
