import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_client.dart';
import '../events/event_providers.dart';
import 'ticket.dart';

final checkInControllerProvider = Provider((ref) => CheckInController(ref));

class CheckInController {
  CheckInController(this.ref);
  final Ref ref;
  Dio get _dio => ref.read(dioProvider);

  Future<TicketVerification> verify(String eventId, String code) async {
    final uri = Uri.tryParse(code);
    if (uri != null &&
        uri.scheme == 'https' &&
        uri.host.isNotEmpty &&
        uri.path == '/events/detail' &&
        (uri.queryParameters['event_id']?.isNotEmpty ?? false) &&
        (uri.queryParameters['promo']?.isNotEmpty ?? false)) {
      return const TicketVerification(status: 'campaign_qr');
    }
    final response = await _dio.get<Map<String, dynamic>>(
      'tickets/verify',
      queryParameters: {'event_id': eventId, 'qr_token': code},
    );
    return TicketVerification.fromJson(response.data!);
  }

  /// Looks up one attendee row by ticket UUID. Used by the detail screen and
  /// manual entry because the backend exposes no check-in detail route.
  Future<AdmissionTicket?> findAttendee(String eventId, String ticketId) async {
    final response = await _dio.get<List<dynamic>>(
      'checkin/attendees',
      queryParameters: {
        'event_id': eventId,
        'q': ticketId,
        'limit': 20,
        'offset': 0,
      },
    );
    for (final row in response.data ?? const <dynamic>[]) {
      final json = row as Map<String, dynamic>;
      if (json['ticket_id'] == ticketId) {
        return AdmissionTicket.fromAttendee(json);
      }
    }
    return null;
  }

  Future<AdmissionTicket> change(
    String eventId,
    String ticketId, {
    required bool undo,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      undo ? 'tickets/undo-check-in' : 'tickets/check-in',
      queryParameters: {'event_id': eventId, 'ticket_id': ticketId},
    );
    ref.invalidate(summaryProvider(eventId));
    return AdmissionTicket.fromJson(response.data!);
  }
}
