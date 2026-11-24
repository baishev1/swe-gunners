class TicketVerification {
  const TicketVerification({
    required this.status,
    this.valid = false,
    this.ticket,
  });

  TicketVerification.fromJson(Map<String, dynamic> json)
    : status = json['status'] as String,
      valid = json['valid'] == true,
      ticket = json['ticket'] == null
          ? null
          : AdmissionTicket.fromJson(json['ticket'] as Map<String, dynamic>);

  final String status;
  final bool valid;
  final AdmissionTicket? ticket;
}

/// A ticket in the backend `TicketResponse` shape, used by verification,
/// check-in and undo.
class AdmissionTicket {
  const AdmissionTicket({
    required this.id,
    required this.name,
    required this.email,
    required this.type,
    required this.status,
    this.checkedInAt,
    this.section,
    this.row,
    this.seat,
  });

  AdmissionTicket.fromJson(Map<String, dynamic> json)
    : id = json['id'] as String,
      name = json['attendee_name'] as String,
      email = json['attendee_email'] as String,
      type = json['ticket_type_name'] as String,
      status = json['status'] as String,
      checkedInAt = json['checked_in_at'] as String?,
      section = json['section'] as String?,
      row = json['row'] as String?,
      seat = json['seat'] as String?;

  /// Maps one row of `GET /checkin/attendees`
  /// (`EventAttendeeResponse`) to the client model.
  AdmissionTicket.fromAttendee(Map<String, dynamic> json)
    : id = json['ticket_id'] as String,
      name = json['attendee_name'] as String,
      email = json['attendee_email'] as String,
      type = json['ticket_type_name'] as String,
      status = json['ticket_status'] as String,
      checkedInAt = json['checked_in_at'] as String?,
      section = json['section'] as String?,
      row = json['row'] as String?,
      seat = json['seat'] as String?;

  final String id, name, email, type, status;
  final String? checkedInAt, section, row, seat;

  /// Formats assigned seat parts, or returns `null` for general admission.
  String? get assignedSeatLabel {
    final parts = [
      section,
      row,
      seat,
    ].whereType<String>().map((s) => s.trim()).where((s) => s.isNotEmpty);
    return parts.isEmpty ? null : parts.join(' / ');
  }
}
