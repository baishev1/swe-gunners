import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_client.dart';
import '../auth/session_controller.dart';
import 'event.dart';

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
  final response = await ref
      .read(dioProvider)
      .get<List<dynamic>>('checkin/events');
  return response.data!
      .map((e) => StaffEvent.fromJson(Map<String, dynamic>.from(e as Map)))
      .toList();
});
final eventProvider = FutureProvider.autoDispose.family<StaffEvent, String>((
  ref,
  id,
) async {
  ref.watch(sessionProvider);
  final response = await ref
      .read(dioProvider)
      .get<Map<String, dynamic>>(
        'events/detail',
        queryParameters: {'event_id': id},
      );
  return StaffEvent.fromJson(response.data!);
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
