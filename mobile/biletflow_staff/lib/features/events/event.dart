class StaffEvent {
  StaffEvent.fromJson(Map<String, dynamic> json)
    : id = json['id'] as String,
      organizerId = json['organizer_id'] as String,
      canUndoCheckIn = json['can_undo_check_in'] == true,
      title = json['title'] as String,
      status = json['status'] as String,
      startsAt = json['start_time'] as String,
      timezone = json['timezone'] as String,
      venue = json['venue']['name'] as String,
      address = json['venue']['address'] as String;
  final String id,
      organizerId,
      title,
      status,
      startsAt,
      timezone,
      venue,
      address;
  final bool canUndoCheckIn;
  bool get cancelled => status == 'cancelled';
}
