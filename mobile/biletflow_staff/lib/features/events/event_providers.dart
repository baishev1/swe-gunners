import 'package:dio/dio.dart';
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
    if (page.length < limit) return events;
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
