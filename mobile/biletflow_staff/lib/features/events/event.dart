class StaffEvent {
  StaffEvent.fromJson(Map<String, dynamic> json)
    : id = json['id'] as String,
      title = json['title'] as String,
      status = json['status'] as String,
      startsAt = json['start_time'] as String,
      timezone = json['timezone'] as String,
      venue = json['venue']['name'] as String,
      address = json['venue']['address'] as String;
  final String id, title, status, startsAt, timezone, venue, address;
  bool get cancelled => status == 'cancelled';
}
