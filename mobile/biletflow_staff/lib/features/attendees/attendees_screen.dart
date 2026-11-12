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

class AttendeesScreen extends ConsumerStatefulWidget {
  const AttendeesScreen({
    super.key,
    required this.event,
    this.embedded = false,
  });
  final StaffEvent event;
  final bool embedded;
  @override
  ConsumerState<AttendeesScreen> createState() => _AttendeesScreenState();
}

class _AttendeesScreenState extends ConsumerState<AttendeesScreen> {
  final _query = TextEditingController();
  final List<AdmissionTicket> _tickets = [];
  Timer? _debounce;
  int _total = 0, _generation = 0;
  bool _busy = false;
  Object? _error;
  String _activeQuery = '';
  @override
  void initState() {
    super.initState();
    _query.addListener(_onQuery);
    _search();
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _query.dispose();
    super.dispose();
  }

  void _onQuery() {
    _debounce?.cancel();
    // Invalidate older responses immediately, before the debounce finishes.
    _generation++;
    setState(() {
      _busy = true;
      _error = null;
    });
    _debounce = Timer(const Duration(milliseconds: 300), () => _search());
  }

  Future<void> _search({bool more = false}) async {
    _debounce?.cancel();
    final generation = ++_generation;
    if (!more) _activeQuery = _query.text.trim();
    setState(() {
      _busy = true;
      _error = null;
      if (!more) _tickets.clear();
    });
    try {
      final response = await ref
          .read(dioProvider)
          .get<Map<String, dynamic>>(
            'checkin/attendees',
            queryParameters: {
              'event_id': widget.event.id,
              'q': _activeQuery,
              'limit': 20,
              'offset': more ? _tickets.length : 0,
            },
          );
      if (!mounted || generation != _generation) return;
      setState(() {
        _total = response.data!['total'] as int;
        _tickets.addAll(
          (response.data!['items'] as List).map(
            (e) => AdmissionTicket.fromJson(e as Map<String, dynamic>),
          ),
        );
      });
    } catch (error) {
      if (mounted && generation == _generation) setState(() => _error = error);
    } finally {
      if (mounted && generation == _generation) setState(() => _busy = false);
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
        suffixBuilder: (_, _, _) => IconButton(
          tooltip: context.l.clearSearch,
          onPressed: _query.clear,
          icon: const Icon(Icons.close_rounded, size: 18),
        ),
        onSubmit: (_) => _search(),
      ),
      if (_error != null) ...[
        ErrorNotice(error: _error!),
        FButton(
          builder: fitButtonLabel,
          size: .lg,
          variant: FButtonVariant.outline,
          onPress: () => _search(),
          child: Text(context.l.retry),
        ),
      ],
      if (_busy)
        const Padding(
          padding: EdgeInsets.all(24),
          child: Center(child: FCircularProgress()),
        ),
      if (!_busy && _error == null) ...[
        Text(
          context.l.attendeeCount(_total),
          style: Theme.of(context).textTheme.bodySmall,
        ),
        if (_tickets.isEmpty)
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
          Material(
            color: context.theme.colors.card,
            borderRadius: BorderRadius.circular(18),
            clipBehavior: Clip.antiAlias,
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
                        TicketScreen(
                          event: widget.event,
                          ticketId: _tickets[i].id,
                        ),
                      );
                      if (mounted) await _search();
                    },
                  ),
                ],
              ],
            ),
          ),
        if (_tickets.length < _total)
          FButton(
            builder: fitButtonLabel,
            size: .lg,
            variant: FButtonVariant.outline,
            onPress: () => _search(more: true),
            child: Text(context.l.loadMore),
          ),
      ],
    ];
    if (widget.embedded) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        spacing: 20,
        children: children,
      );
    }
    return AppPage(title: context.l.attendees, children: children);
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
            foregroundColor: context.theme.colors.mutedForeground,
            child: Text(
              ticket.name.characters.first,
              style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              spacing: 6,
              children: [
                Text(
                  ticket.name,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                Text(ticket.type, style: Theme.of(context).textTheme.bodySmall),
                StatusTag(status: ticket.status),
              ],
            ),
          ),
          const Padding(
            padding: EdgeInsets.only(top: 8),
            child: Icon(Icons.chevron_right_rounded, size: 20),
          ),
        ],
      ),
    ),
  );
}
