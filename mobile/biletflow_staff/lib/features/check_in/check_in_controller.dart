import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_client.dart';
import '../events/event_providers.dart';

final checkInControllerProvider = Provider((ref) => CheckInController(ref));

class CheckInController {
  CheckInController(this.ref);
  final Ref ref;
  Dio get _dio => ref.read(dioProvider);

  Future<Map<String, dynamic>> verify(String eventId, String code) async {
    final response = await _dio.post<Map<String, dynamic>>(
      'checkin/verify',
      data: {'event_id': eventId, 'qr_code': code},
    );
    return response.data!;
  }

  Future<Map<String, dynamic>> change(
    String eventId,
    String ticketId, {
    required bool undo,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      undo ? 'checkin/undo' : 'checkin/admit',
      data: {'event_id': eventId, 'ticket_id': ticketId},
    );
    ref.invalidate(summaryProvider(eventId));
    return response.data!;
  }
}
