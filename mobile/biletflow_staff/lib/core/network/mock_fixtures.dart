const demoEventId = '019a2000-0000-7000-8000-000000000001';
const upcomingEventId = '019a2000-0000-7000-8000-000000000002';
const cancelledEventId = '019a2000-0000-7000-8000-000000000003';
const unassignedEventId = '019a2000-0000-7000-8000-000000000004';
const demoToken = 'demo-access-token';
const demoEmail = 'staff@biletflow.demo';
const demoPassword = 'Demo123!';
const demoUser = {
  'id': '019a2000-0000-7000-8000-000000000010',
  'email': demoEmail,
  'full_name': 'Alex Demo',
  'role': 'attendee',
  'is_email_verified': true,
};

String _day(int offset) => DateTime.now()
    .toUtc()
    .add(Duration(days: offset))
    .toIso8601String()
    .substring(0, 10);

/// Mock events mirror the backend `AssignedEventResponse` shape. Dates are
/// relative to the current day so the demo never starts with past events.
List<Map<String, dynamic>> eventFixtures() => [
  for (final (id, title, status, dayOffset) in [
    (demoEventId, 'Almaty Creative Night / Шығармашылық кеш', 'published', 2),
    (upcomingEventId, 'Astana Tech Meetup', 'published', 20),
    (cancelledEventId, 'Autumn Open Air', 'cancelled', 5),
    (unassignedEventId, 'Private Partner Summit', 'published', 12),
  ])
    {
      'id': id,
      'organizer_id': '019a2000-0000-7000-8000-000000000011',
      // Ordinary staff can undo the demo event, but not the meetup.
      'can_undo_check_in': id == demoEventId,
      'title': title,
      'description': 'A fictional event for the Biletflow staff demo.',
      'category': 'community',
      'venue_id': '019a2000-0000-7000-8000-000000000012',
      'start_time': '${_day(dayOffset)}T18:00:00+05:00',
      'end_time': '${_day(dayOffset)}T22:00:00+05:00',
      'timezone': 'Asia/Almaty',
      'capacity': 200,
      'visibility': 'private',
      'is_assigned_seating': id == demoEventId,
      'registration_start_time': null,
      'registration_end_time': null,
      'cover_image_url': null,
      'status': status,
      'venue': {
        'id': '019a2000-0000-7000-8000-000000000012',
        'name': 'Demo Hall',
        'address': 'Almaty, Demo Avenue 10',
        'created_at': '2026-10-01T10:00:00Z',
        'updated_at': '2026-10-01T10:00:00Z',
      },
      'created_at': '2026-10-01T10:00:00Z',
      'updated_at': '2026-10-01T10:00:00Z',
    },
];

/// Mock tickets carry backend `TicketResponse` fields plus demo-only
/// `qr_token` and order status used to emulate the server guards.
List<Map<String, dynamic>> ticketFixtures() => [
  for (final (number, name, status, code, eventId, orderStatus) in [
    (1, 'Аружан Демо', 'valid', 'DEMO-VALID', demoEventId, 'paid'),
    (2, 'Данияр Демо', 'checked_in', 'DEMO-USED', demoEventId, 'paid'),
    (3, 'Sam Demo', 'cancelled', 'DEMO-CANCELLED', demoEventId, 'cancelled'),
    (4, 'Мария Демо', 'refunded', 'DEMO-REFUNDED', demoEventId, 'refunded'),
    (5, 'Taylor Demo', 'valid', 'DEMO-OTHER', upcomingEventId, 'paid'),
    (6, 'Robin Demo', 'checked_in', 'DEMO-NO-UNDO', demoEventId, 'paid'),
    (7, 'Kai Demo', 'valid', 'DEMO-GENERAL', demoEventId, 'paid'),
  ])
    {
      'id': '019a2000-0000-7000-8000-${number.toString().padLeft(12, '0')}',
      'order_id':
          '019a2000-0001-7000-8000-${number.toString().padLeft(12, '0')}',
      'order_item_id':
          '019a2000-0002-7000-8000-${number.toString().padLeft(12, '0')}',
      'event_id': eventId,
      'ticket_type_id':
          '019a2000-0003-7000-8000-${number.toString().padLeft(12, '0')}',
      'ticket_type_name': number == 1 ? 'VIP' : 'Standard',
      'attendee_name': name,
      'attendee_email': 'guest$number@example.test',
      'qr_token': code,
      'status': status,
      'checked_in_at': status == 'checked_in' ? '2026-10-27T13:15:00Z' : null,
      'section': number == 1 ? 'A' : null,
      'row': number == 1 ? '2' : null,
      'seat': number == 1 ? '12' : null,
      'order_status': orderStatus,
      'created_at': '2026-10-01T10:00:00Z',
      'updated_at': '2026-10-01T10:00:00Z',
    },
];
