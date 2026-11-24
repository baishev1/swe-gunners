// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appName => 'Biletflow Staff';

  @override
  String get demo => 'Demo data · online simulation';

  @override
  String get signIn => 'Sign in';

  @override
  String get email => 'Email';

  @override
  String get password => 'Password';

  @override
  String get showPassword => 'Show password';

  @override
  String get hidePassword => 'Hide password';

  @override
  String get requiredField => 'This field is required.';

  @override
  String get invalidEmail => 'Enter a valid email address.';

  @override
  String get forgotPassword => 'Forgot password?';

  @override
  String get resetPassword => 'Reset password';

  @override
  String get sendReset => 'Send reset link';

  @override
  String get resetSent =>
      'If this account exists, a reset link will be sent. In demo mode no email is sent.';

  @override
  String get noEvents => 'No events assigned yet.';

  @override
  String get refresh => 'Refresh';

  @override
  String get retry => 'Retry';

  @override
  String get back => 'Back';

  @override
  String get settings => 'Settings';

  @override
  String get language => 'Language';

  @override
  String get logout => 'Log out';

  @override
  String get account => 'Account';

  @override
  String get overview => 'Event overview';

  @override
  String get registered => 'Registered';

  @override
  String get remaining => 'Not arrived';

  @override
  String get scanTicket => 'Scan ticket';

  @override
  String get eventCancelled => 'This event is cancelled. Admission is closed.';

  @override
  String get published => 'Published';

  @override
  String get cancelled => 'Cancelled';

  @override
  String get openCamera => 'Open camera';

  @override
  String get closeCamera => 'Close camera';

  @override
  String get cameraError =>
      'Camera unavailable or permission denied. Allow camera access in device settings, or enter a code below.';

  @override
  String get torch => 'Toggle torch';

  @override
  String get manualCode => 'Ticket ID or QR token';

  @override
  String get manualCodeHint =>
      'Paste the ticket UUID or 64-character QR token.';

  @override
  String get verify => 'Verify ticket';

  @override
  String get demoScans => 'Demo scan scenarios';

  @override
  String get valid => 'Valid ticket';

  @override
  String get invalid => 'Invalid ticket';

  @override
  String get refunded => 'Refunded ticket';

  @override
  String get checked_in => 'Already used';

  @override
  String get wrong_event => 'Ticket for another event';

  @override
  String get campaign_qr => 'Campaign QR · no admission';

  @override
  String get verification => 'Verification result';

  @override
  String get checkIn => 'Check in';

  @override
  String get admitted => 'Check-in recorded';

  @override
  String get scanNext => 'Scan next ticket';

  @override
  String get undo => 'Undo check-in';

  @override
  String get undoTitle => 'Undo this check-in?';

  @override
  String get undoHint =>
      'The ticket will become available for admission again.';

  @override
  String get undoDone => 'Check-in reversed';

  @override
  String get confirm => 'Confirm';

  @override
  String get cancel => 'Cancel';

  @override
  String get attendees => 'Attendees';

  @override
  String get searchHint => 'Name, email or ticket ID';

  @override
  String get noResults => 'No attendees found.';

  @override
  String get loadMore => 'Load more';

  @override
  String get ticket => 'Ticket';

  @override
  String get ticketType => 'Ticket type';

  @override
  String get seat => 'Section / row / seat';

  @override
  String get generalAdmission => 'General admission';

  @override
  String get checkInTime => 'Check-in time';

  @override
  String get offline => 'No connection. Admission requires an online response.';

  @override
  String get serverError => 'Service unavailable. Please try again.';

  @override
  String get unauthorized => 'Your session expired. Please sign in again.';

  @override
  String get forbidden => 'You do not have permission for this action.';

  @override
  String get notFound => 'This record is unavailable.';

  @override
  String get conflict => 'Ticket status changed. Refresh before trying again.';

  @override
  String get badCredentials => 'Incorrect email or password.';

  @override
  String get storageError => 'Unable to access your saved session.';

  @override
  String get genericError => 'Something went wrong. Please try again.';

  @override
  String get demoControls => 'Demo controls';

  @override
  String get normal => 'Normal connection';

  @override
  String get offlineMode => 'Simulate offline';

  @override
  String get serverMode => 'Simulate server error';

  @override
  String get emptyAssignments => 'Show no assignments';

  @override
  String get revokeAssignment => 'Revoke event access';

  @override
  String get expireSession => 'Expire session';

  @override
  String get resetDemo => 'Reset demo data';

  @override
  String get permissionDenied => 'Undo not permitted';

  @override
  String get resetHint => 'Enter the email used for your staff account.';

  @override
  String get demoShort => 'Demo';

  @override
  String get overviewTab => 'Overview';

  @override
  String get scanTab => 'Scan';

  @override
  String get guestsTab => 'Guests';

  @override
  String get welcomeTitle => 'Welcome to\nyour next event.';

  @override
  String get welcomeBody =>
      'Sign in to check tickets and keep the door moving.';

  @override
  String get yourEvents => 'Your events';

  @override
  String get chooseEvent => 'Choose where you’re checking in today.';

  @override
  String get attendance => 'Attendance';

  @override
  String get admittedLabel => 'Admitted';

  @override
  String ofRegistered(String total) {
    return 'of $total registered';
  }

  @override
  String get readyToScan => 'Ready for the next guest';

  @override
  String get scanGuide => 'Position the ticket QR code inside the frame.';

  @override
  String get manualEntry => 'Enter code manually';

  @override
  String get demoChoose => 'Try a demo ticket';

  @override
  String get checkingTicket => 'Checking ticket…';

  @override
  String get admissionHint => 'Confirm entry to mark this ticket as used.';

  @override
  String get admittedHint =>
      'Entry is recorded. You’re ready for the next guest.';

  @override
  String get usedHint => 'This ticket has already been checked in.';

  @override
  String get blockedHint =>
      'Do not admit this ticket. Check the details or ask the event organizer.';

  @override
  String get noGuestsHint => 'Try another name, email or ticket ID.';

  @override
  String get preferences => 'Preferences';

  @override
  String get demoToolsHint => 'Test ticket states and connection issues.';

  @override
  String get signedInAs => 'Signed in as event staff';

  @override
  String get eventDetails => 'Event details';

  @override
  String get logoutConfirm => 'Log out of this account?';

  @override
  String get logoutHint => 'You’ll need to sign in again to check tickets.';

  @override
  String get clearSearch => 'Clear search';

  @override
  String get demoLoginHint =>
      'The demo account is filled in. Sign in to explore.';

  @override
  String get ticketNotFound => 'Ticket not found';

  @override
  String get pending => 'Payment pending';

  @override
  String get invalidOrder => 'Order not eligible';

  @override
  String get validationError => 'Check the entered information and try again.';
}
