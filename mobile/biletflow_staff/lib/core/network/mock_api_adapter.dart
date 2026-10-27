import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'mock_fixtures.dart';

const useMockApi = bool.fromEnvironment('USE_MOCK_API', defaultValue: true);
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

  Map<String, dynamic> summary(String eventId) {
    final records = tickets.where((t) => t['event_id'] == eventId);
    final active = records.where(
      (t) => ['valid', 'checked_in'].contains(t['status']),
    );
    return {
      'event_id': eventId,
      'registered': active.length,
      'checked_in': active.where((t) => t['status'] == 'checked_in').length,
    };
  }

  Map<String, dynamic> publicTicket(Map<String, dynamic> ticket) => {
    for (final entry in ticket.entries)
      if (entry.key != 'qr_code') entry.key: entry.value,
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
      return error(403, 'event_access_denied');
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
    if (!path.startsWith('checkin/')) return error(404, 'route_not_found');
    final eventId =
        (method == 'GET' ? query['event_id'] : body['event_id']) as String?;
    final denied = eventAccess(eventId);
    if (denied != null) return denied;
    final event = events.firstWhere((e) => e['id'] == eventId);

    if (path == 'checkin/summary' && method == 'GET') {
      return json(summary(eventId!));
    }
    if (path == 'checkin/attendees' && method == 'GET') {
      final q = (query['q'] ?? '').toLowerCase().trim();
      final matches = tickets
          .where(
            (t) =>
                t['event_id'] == eventId &&
                [
                  'attendee_name',
                  'attendee_email',
                  'id',
                ].any((key) => (t[key] as String).toLowerCase().contains(q)),
          )
          .toList();
      final offset = (int.tryParse(query['offset'] ?? '') ?? 0).clamp(
        0,
        100000,
      );
      final limit = (int.tryParse(query['limit'] ?? '') ?? 3).clamp(1, 100);
      return json({
        'items': matches.skip(offset).take(limit).map(publicTicket).toList(),
        'total': matches.length,
        'limit': limit,
        'offset': offset,
      });
    }
    if (path == 'checkin/tickets/detail' && method == 'GET') {
      final found = tickets.where(
        (t) => t['id'] == query['ticket_id'] && t['event_id'] == eventId,
      );
      return found.isEmpty
          ? error(404, 'ticket_not_found')
          : json(publicTicket(found.first));
    }
    if (event['status'] == 'cancelled') return error(409, 'event_cancelled');
    if (path == 'checkin/verify' && method == 'POST') {
      final code = body['qr_code'];
      if (code is! String || code.trim().isEmpty) {
        return error(422, 'invalid_code');
      }
      if (code.startsWith('https://') || code.startsWith('http://')) {
        return json({
          'result': 'campaign_qr',
          'ticket': null,
          'can_check_in': false,
          'can_undo': false,
        });
      }
      final matches = tickets.where((t) => t['qr_code'] == code);
      if (matches.isEmpty) {
        return json({
          'result': 'invalid',
          'ticket': null,
          'can_check_in': false,
          'can_undo': false,
        });
      }
      final ticket = matches.first;
      if (ticket['event_id'] != eventId) {
        return json({
          'result': 'wrong_event',
          'ticket': null,
          'can_check_in': false,
          'can_undo': false,
        });
      }
      return json({
        'result': ticket['status'],
        'ticket': publicTicket(ticket),
        'can_check_in': ticket['status'] == 'valid',
        'can_undo':
            ticket['status'] == 'checked_in' && ticket['can_undo'] == true,
      });
    }
    if (['checkin/admit', 'checkin/undo'].contains(path) && method == 'POST') {
      final found = tickets.where(
        (t) => t['id'] == body['ticket_id'] && t['event_id'] == eventId,
      );
      if (found.isEmpty) return error(404, 'ticket_not_found');
      final ticket = found.first;
      if (path.endsWith('/undo')) {
        if (ticket['can_undo'] != true) return error(403, 'undo_forbidden');
        if (ticket['status'] != 'checked_in') {
          return error(409, 'not_checked_in');
        }
        ticket['status'] = 'valid';
        ticket['checked_in_at'] = null;
      } else {
        if (ticket['status'] != 'valid') return error(409, 'ticket_not_valid');
        ticket['status'] = 'checked_in';
        ticket['checked_in_at'] = DateTime.now().toUtc().toIso8601String();
      }
      return json({
        'ticket': publicTicket(ticket),
        'summary': summary(eventId!),
      });
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
