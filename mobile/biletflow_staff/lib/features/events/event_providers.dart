import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_client.dart';
import '../auth/session_controller.dart';
import 'event.dart';

/// Sorts active and upcoming events first (earliest start first), followed by
/// completed events (most recent first).
List<StaffEvent> sortStaffEvents(List<StaffEvent> events, {DateTime? now}) {
  final current = (now ?? DateTime.now()).toUtc();
  bool isCompleted(StaffEvent event) {
    final end = DateTime.tryParse(event.endsAt ?? '')?.toUtc();
    if (end != null) return end.isBefore(current);
    final start = DateTime.tryParse(event.startsAt)?.toUtc();
    return start != null && start.isBefore(current);
  }

  final sorted = List<StaffEvent>.of(events);
  sorted.sort((a, b) {
    final aPast = isCompleted(a);
    final bPast = isCompleted(b);
    if (aPast != bPast) return aPast ? 1 : -1;
    final aStart = DateTime.tryParse(a.startsAt)?.toUtc();
    final bStart = DateTime.tryParse(b.startsAt)?.toUtc();
    if (aStart == null || bStart == null) return a.id.compareTo(b.id);
    final byTime = aPast ? bStart.compareTo(aStart) : aStart.compareTo(bStart);
    return byTime != 0 ? byTime : a.id.compareTo(b.id);
  });
  return sorted;
}

final accountProvider = FutureProvider.autoDispose<Map<String, dynamic>>((
  ref,
) async {
  ref.watch(sessionProvider);
  final response = await ref
      .read(dioProvider)
      .get<Map<String, dynamic>>('auth/me');
  return response.data!;
});
final eventsProvider = FutureProvider.autoDispose<List<StaffEvent>>((
  ref,
) async {
  ref.watch(sessionProvider);
  final dio = ref.read(dioProvider);
  const limit = 50;
  final events = <StaffEvent>[];
  while (true) {
    final response = await dio.get<List<dynamic>>(
      'checkin/events',
      queryParameters: {'limit': limit, 'offset': events.length},
    );
    final page = response.data!;
    events.addAll(
      page.map((e) => StaffEvent.fromJson(e as Map<String, dynamic>)),
    );
    if (page.length < limit) return sortStaffEvents(events);
  }
});
final eventProvider = FutureProvider.autoDispose.family<StaffEvent, String>((
  ref,
  id,
) async {
  final events = await ref.watch(eventsProvider.future);
  for (final event in events) {
    if (event.id == id) return event;
  }
  final request = RequestOptions(path: 'checkin/events');
  throw DioException.badResponse(
    statusCode: 404,
    requestOptions: request,
    response: Response<void>(requestOptions: request, statusCode: 404),
  );
});
final summaryProvider = FutureProvider.autoDispose
    .family<Map<String, dynamic>, String>((ref, id) async {
      ref.watch(sessionProvider);
      final response = await ref
          .read(dioProvider)
          .get<Map<String, dynamic>>(
            'checkin/summary',
            queryParameters: {'event_id': id},
          );
      return response.data!;
    });
