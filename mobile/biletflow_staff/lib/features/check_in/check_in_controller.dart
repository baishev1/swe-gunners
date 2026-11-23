import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_client.dart';
import '../../core/network/mock_api_adapter.dart';
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

  Future<AdmissionTicket> change(
    String eventId,
    String ticketId, {
    required bool undo,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      undo ? 'tickets/undo-check-in' : 'tickets/check-in',
      queryParameters: {'event_id': eventId, 'ticket_id': ticketId},
    );
    if (useMockApi) ref.invalidate(summaryProvider(eventId));
    return AdmissionTicket.fromJson(response.data!);
  }
}
