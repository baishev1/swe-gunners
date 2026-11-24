import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'mock_fixtures.dart';

/// Whether the demo transport is active. Tests override this instead of
/// depending on a compile-time flag.
final useMockApiProvider = Provider<bool>(
  (ref) => const bool.fromEnvironment('USE_MOCK_API'),
);
final mockServerProvider = Provider((ref) => MockServer());

enum DemoConnection { normal, offline, serverError }

class MockServer {
  MockServer({this.latency = const Duration(milliseconds: 350)});
  final Duration latency;
  List<Map<String, dynamic>> events = eventFixtures();
  List<Map<String, dynamic>> tickets = ticketFixtures();
  DemoConnection connection = DemoConnection.normal;
  bool emptyAssignments = false;
  bool revoked = false;
  bool expired = false;

  void reset() {
    events = eventFixtures();
    tickets = ticketFixtures();
    connection = DemoConnection.normal;
    emptyAssignments = revoked = expired = false;
  }

  /// Mirrors `GET /checkin/summary`: registered/checked-in counts only for
  /// paid orders, same as the backend query.
  Map<String, dynamic> summary(String eventId) {
    final records = tickets.where(
      (t) => t['event_id'] == eventId && t['order_status'] == 'paid',
    );
    final active = records.where(
      (t) => ['valid', 'checked_in'].contains(t['status']),
    );
    return {
      'event_id': eventId,
      'registered': active.length,
      'checked_in': active.where((t) => t['status'] == 'checked_in').length,
    };
  }

  /// `TicketResponse` shape used by verify, check-in and undo.
  Map<String, dynamic> ticketResponse(Map<String, dynamic> ticket) => {
    'id': ticket['id'],
    'order_id': ticket['order_id'],
    'order_item_id': ticket['order_item_id'],
    'event_id': ticket['event_id'],
    'ticket_type_id': ticket['ticket_type_id'],
    'ticket_type_name': ticket['ticket_type_name'],
    'attendee_name': ticket['attendee_name'],
    'attendee_email': ticket['attendee_email'],
    'qr_token': ticket['qr_token'],
    'status': ticket['status'],
    'checked_in_at': ticket['checked_in_at'],
    'section': ticket['section'],
    'row': ticket['row'],
    'seat': ticket['seat'],
    'created_at': ticket['created_at'],
    'updated_at': ticket['updated_at'],
  };

  /// `EventAttendeeResponse` shape used by `GET /checkin/attendees`.
  Map<String, dynamic> attendeeResponse(Map<String, dynamic> ticket) => {
    'ticket_id': ticket['id'],
    'order_id': ticket['order_id'],
    'attendee_name': ticket['attendee_name'],
    'attendee_email': ticket['attendee_email'],
    'ticket_type_id': ticket['ticket_type_id'],
    'ticket_type_name': ticket['ticket_type_name'],
    'ticket_status': ticket['status'],
    'order_status': ticket['order_status'],
    'checked_in_at': ticket['checked_in_at'],
    'section': ticket['section'],
    'row': ticket['row'],
    'seat': ticket['seat'],
    'created_at': ticket['created_at'],
  };

  ResponseBody json(Object? data, [int status = 200]) =>
      ResponseBody.fromString(
        jsonEncode(data),
        status,
        headers: {
          Headers.contentTypeHeader: [Headers.jsonContentType],
        },
      );
  ResponseBody error(int status, String detail) =>
      json({'detail': detail}, status);

  ResponseBody? eventAccess(String? id) {
    if (id == null || !events.any((e) => e['id'] == id)) {
      return error(404, 'event_not_found');
    }
    if (id == unassignedEventId || revoked || emptyAssignments) {
      return error(404, 'event_access_denied');
    }
    return null;
  }

  Future<ResponseBody> handle(RequestOptions request) async {
    await Future<void>.delayed(latency);
    if (connection == DemoConnection.offline) {
      throw DioException.connectionError(
        requestOptions: request,
        reason: 'demo_offline',
      );
    }
    if (connection == DemoConnection.serverError) {
      return error(503, 'service_unavailable');
    }
    final path = request.uri.path.replaceFirst(RegExp(r'^/api/v1/?'), '');
    final method = request.method;
    final query = request.uri.queryParameters;
    final body = request.data is Map
        ? Map<String, dynamic>.from(request.data as Map)
        : <String, dynamic>{};

    if (path == 'auth/login' && method == 'POST') {
      if (body['email'] != demoEmail || body['password'] != demoPassword) {
        return error(401, 'Invalid email or password');
      }
      expired = false;
      return json({'access_token': demoToken, 'token_type': 'bearer'});
    }
    if (path == 'auth/forgot-password' && method == 'POST') {
      return ResponseBody.fromString('', 204);
    }
    if (expired || request.headers['Authorization'] != 'Bearer $demoToken') {
      return error(401, 'token_invalid');
    }
    if (path == 'auth/me' && method == 'GET') return json(demoUser);

    if (path == 'checkin/events' && method == 'GET') {
      return json(
        emptyAssignments || revoked
            ? []
            : events
                  .where(
                    (e) =>
                        e['id'] != unassignedEventId &&
                        e['status'] != 'cancelled',
                  )
                  .skip(int.tryParse(query['offset'] ?? '') ?? 0)
                  .take(int.tryParse(query['limit'] ?? '') ?? 50)
                  .toList(),
      );
    }
    if (path == 'events/detail' && method == 'GET') {
      final id = query['event_id'];
      final denied = eventAccess(id);
      if (denied != null) return denied;
      return json(events.firstWhere((e) => e['id'] == id));
    }
    if (!path.startsWith('checkin/') && !path.startsWith('tickets/')) {
      return error(404, 'route_not_found');
    }
    final eventId = query['event_id'];
    final denied = eventAccess(eventId);
    if (denied != null) return denied;
    final event = events.firstWhere((e) => e['id'] == eventId);
    if (event['status'] == 'cancelled') {
      return error(400, 'Cannot check in to a cancelled event');
    }

    if (path == 'checkin/summary' && method == 'GET') {
      return json(summary(eventId!));
    }
    if (path == 'checkin/attendees' && method == 'GET') {
      final q = (query['q'] ?? '').toLowerCase().trim();
      final matches =
          tickets
              .where(
                (t) =>
                    t['event_id'] == eventId &&
                    ['attendee_name', 'attendee_email', 'id'].any(
                      (key) => (t[key] as String).toLowerCase().contains(q),
                    ),
              )
              .toList()
            ..sort((a, b) {
              final byName = (a['attendee_name'] as String).compareTo(
                b['attendee_name'] as String,
              );
              return byName != 0
                  ? byName
                  : (a['id'] as String).compareTo(b['id'] as String);
            });
      final offset = (int.tryParse(query['offset'] ?? '') ?? 0).clamp(
        0,
        100000,
      );
      final limit = (int.tryParse(query['limit'] ?? '') ?? 50).clamp(1, 100);
      return json(
        matches
            .skip(offset)
            .take(limit)
            .map(attendeeResponse)
            .toList(growable: false),
      );
    }
    if (path == 'tickets/verify' && method == 'GET') {
      final code = query['qr_token'];
      if (code == null) return error(422, 'invalid_code');
      final ticket = tickets
          .where((t) => t['qr_token'] == code && t['event_id'] == eventId)
          .firstOrNull;
      final orderStatus = ticket?['order_status'] as String?;
      final status = ticket == null
          ? 'not_found'
          : orderStatus != 'paid'
          ? orderStatus!
          : ticket['status'] as String;
      return json({
        'valid': status == 'valid',
        'status': status,
        'ticket': ticket == null ? null : ticketResponse(ticket),
        'message': 'Ticket is $status',
      });
    }
    if (['tickets/check-in', 'tickets/undo-check-in'].contains(path) &&
        method == 'POST') {
      final found = tickets.where(
        (t) => t['id'] == query['ticket_id'] && t['event_id'] == eventId,
      );
      if (found.isEmpty) return error(404, 'Ticket not found for this event');
      final ticket = found.first;
      if (ticket['order_status'] != 'paid') {
        return error(400, 'Ticket is not eligible for admission');
      }
      if (path == 'tickets/undo-check-in') {
        if (event['can_undo_check_in'] != true) {
          return error(403, 'Check-in reversal is not permitted');
        }
        if (ticket['status'] != 'checked_in') {
          return error(400, 'Ticket is not checked in');
        }
        ticket['status'] = 'valid';
        ticket['checked_in_at'] = null;
      } else {
        if (ticket['status'] != 'valid') {
          return error(
            400,
            'Ticket is already checked in or is not eligible for admission',
          );
        }
        ticket['status'] = 'checked_in';
        ticket['checked_in_at'] = DateTime.now().toUtc().toIso8601String();
      }
      ticket['updated_at'] = DateTime.now().toUtc().toIso8601String();
      return json(ticketResponse(ticket));
    }
    return error(404, 'route_not_found');
  }
}

class MockApiAdapter implements HttpClientAdapter {
  MockApiAdapter(this.server);
  final MockServer server;
  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) => server.handle(options);
  @override
  void close({bool force = false}) {}
}
