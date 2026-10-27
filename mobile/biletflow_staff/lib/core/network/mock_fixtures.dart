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

List<Map<String, dynamic>> eventFixtures() => [
  for (final (id, title, status, date) in [
    (
      demoEventId,
      'Almaty Creative Night / Шығармашылық кеш',
      'published',
      '2026-10-27',
    ),
    (upcomingEventId, 'Astana Tech Meetup', 'published', '2026-11-15'),
    (cancelledEventId, 'Autumn Open Air', 'cancelled', '2026-10-30'),
    (unassignedEventId, 'Private Partner Summit', 'published', '2026-11-20'),
  ])
    {
      'id': id,
      'organizer_id': '019a2000-0000-7000-8000-000000000011',
      'title': title,
      'description': 'A fictional event for the Biletflow staff demo.',
      'category': 'community',
      'venue_id': '019a2000-0000-7000-8000-000000000012',
      'start_time': '${date}T18:00:00+05:00',
      'end_time': '${date}T22:00:00+05:00',
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

List<Map<String, dynamic>> ticketFixtures() => [
  for (final (number, name, status, code, eventId, canUndo) in [
    (1, 'Аружан Демо', 'valid', 'DEMO-VALID', demoEventId, true),
    (2, 'Данияр Демо', 'checked_in', 'DEMO-USED', demoEventId, true),
    (3, 'Sam Demo', 'cancelled', 'DEMO-CANCELLED', demoEventId, false),
    (4, 'Мария Демо', 'refunded', 'DEMO-REFUNDED', demoEventId, false),
    (5, 'Taylor Demo', 'valid', 'DEMO-OTHER', upcomingEventId, true),
    (6, 'Robin Demo', 'checked_in', 'DEMO-NO-UNDO', demoEventId, false),
    (7, 'Kai Demo', 'valid', 'DEMO-GENERAL', demoEventId, true),
  ])
    {
      'id': '019a2000-0000-7000-8000-${number.toString().padLeft(12, '0')}',
      'event_id': eventId,
      'attendee_name': name,
      'attendee_email': 'guest$number@example.test',
      'ticket_type_name': number == 1 ? 'VIP' : 'Standard',
      'status': status,
      'checked_in_at': status == 'checked_in' ? '2026-10-27T13:15:00Z' : null,
      'section': number == 1 ? 'A' : null,
      'row': number == 1 ? '2' : null,
      'seat': number == 1 ? '12' : null,
      'can_undo': canUndo,
      'qr_code': code,
    },
];
