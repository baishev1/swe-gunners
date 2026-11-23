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

class AdmissionTicket {
  AdmissionTicket.fromJson(Map<String, dynamic> json)
    : id = json['id'] as String,
      name = json['attendee_name'] as String,
      email = json['attendee_email'] as String,
      type = json['ticket_type_name'] as String,
      status = json['status'] as String,
      checkedInAt = json['checked_in_at'] as String?,
      section = json['section'] as String?,
      row = json['row'] as String?,
      seat = json['seat'] as String?,
      canUndo = json['can_undo'] == true;
  final String id, name, email, type, status;
  final String? checkedInAt, section, row, seat;
  final bool canUndo;
}
