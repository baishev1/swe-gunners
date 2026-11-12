import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_kk.dart';
import 'app_localizations_ru.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
    : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations)!;
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
        delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('kk'),
    Locale('ru'),
    Locale('en'),
  ];

  /// No description provided for @appName.
  ///
  /// In en, this message translates to:
  /// **'Biletflow Staff'**
  String get appName;

  /// No description provided for @demo.
  ///
  /// In en, this message translates to:
  /// **'Demo data · online simulation'**
  String get demo;

  /// No description provided for @signIn.
  ///
  /// In en, this message translates to:
  /// **'Sign in'**
  String get signIn;

  /// No description provided for @signInHint.
  ///
  /// In en, this message translates to:
  /// **'Your event, ready at the door.'**
  String get signInHint;

  /// No description provided for @email.
  ///
  /// In en, this message translates to:
  /// **'Email'**
  String get email;

  /// No description provided for @password.
  ///
  /// In en, this message translates to:
  /// **'Password'**
  String get password;

  /// No description provided for @showPassword.
  ///
  /// In en, this message translates to:
  /// **'Show password'**
  String get showPassword;

  /// No description provided for @hidePassword.
  ///
  /// In en, this message translates to:
  /// **'Hide password'**
  String get hidePassword;

  /// No description provided for @requiredField.
  ///
  /// In en, this message translates to:
  /// **'This field is required.'**
  String get requiredField;

  /// No description provided for @invalidEmail.
  ///
  /// In en, this message translates to:
  /// **'Enter a valid email address.'**
  String get invalidEmail;

  /// No description provided for @forgotPassword.
  ///
  /// In en, this message translates to:
  /// **'Forgot password?'**
  String get forgotPassword;

  /// No description provided for @resetPassword.
  ///
  /// In en, this message translates to:
  /// **'Reset password'**
  String get resetPassword;

  /// No description provided for @sendReset.
  ///
  /// In en, this message translates to:
  /// **'Send reset link'**
  String get sendReset;

  /// No description provided for @resetSent.
  ///
  /// In en, this message translates to:
  /// **'If this account exists, a reset link will be sent. In demo mode no email is sent.'**
  String get resetSent;

  /// No description provided for @demoCredentials.
  ///
  /// In en, this message translates to:
  /// **'Demo: staff@biletflow.demo / Demo123!'**
  String get demoCredentials;

  /// No description provided for @events.
  ///
  /// In en, this message translates to:
  /// **'Assigned events'**
  String get events;

  /// No description provided for @eventsHint.
  ///
  /// In en, this message translates to:
  /// **'Choose an event to start welcoming guests.'**
  String get eventsHint;

  /// No description provided for @noEvents.
  ///
  /// In en, this message translates to:
  /// **'No events assigned yet.'**
  String get noEvents;

  /// No description provided for @refresh.
  ///
  /// In en, this message translates to:
  /// **'Refresh'**
  String get refresh;

  /// No description provided for @retry.
  ///
  /// In en, this message translates to:
  /// **'Retry'**
  String get retry;

  /// No description provided for @back.
  ///
  /// In en, this message translates to:
  /// **'Back'**
  String get back;

  /// No description provided for @settings.
  ///
  /// In en, this message translates to:
  /// **'Settings'**
  String get settings;

  /// No description provided for @language.
  ///
  /// In en, this message translates to:
  /// **'Language'**
  String get language;

  /// No description provided for @logout.
  ///
  /// In en, this message translates to:
  /// **'Log out'**
  String get logout;

  /// No description provided for @account.
  ///
  /// In en, this message translates to:
  /// **'Account'**
  String get account;

  /// No description provided for @overview.
  ///
  /// In en, this message translates to:
  /// **'Event overview'**
  String get overview;

  /// No description provided for @registered.
  ///
  /// In en, this message translates to:
  /// **'Registered'**
  String get registered;

  /// No description provided for @checkedIn.
  ///
  /// In en, this message translates to:
  /// **'Checked in'**
  String get checkedIn;

  /// No description provided for @remaining.
  ///
  /// In en, this message translates to:
  /// **'Not arrived'**
  String get remaining;

  /// No description provided for @scanTicket.
  ///
  /// In en, this message translates to:
  /// **'Scan ticket'**
  String get scanTicket;

  /// No description provided for @findAttendee.
  ///
  /// In en, this message translates to:
  /// **'Find attendee'**
  String get findAttendee;

  /// No description provided for @venue.
  ///
  /// In en, this message translates to:
  /// **'Venue'**
  String get venue;

  /// No description provided for @eventCancelled.
  ///
  /// In en, this message translates to:
  /// **'This event is cancelled. Admission is closed.'**
  String get eventCancelled;

  /// No description provided for @published.
  ///
  /// In en, this message translates to:
  /// **'Published'**
  String get published;

  /// No description provided for @cancelled.
  ///
  /// In en, this message translates to:
  /// **'Cancelled'**
  String get cancelled;

  /// No description provided for @upcoming.
  ///
  /// In en, this message translates to:
  /// **'Upcoming'**
  String get upcoming;

  /// No description provided for @scannerHint.
  ///
  /// In en, this message translates to:
  /// **'Scan an admission QR code. Campaign QR codes do not grant entry.'**
  String get scannerHint;

  /// No description provided for @openCamera.
  ///
  /// In en, this message translates to:
  /// **'Open camera'**
  String get openCamera;

  /// No description provided for @closeCamera.
  ///
  /// In en, this message translates to:
  /// **'Close camera'**
  String get closeCamera;

  /// No description provided for @cameraError.
  ///
  /// In en, this message translates to:
  /// **'Camera unavailable or permission denied. Allow camera access in device settings, or enter a code below.'**
  String get cameraError;

  /// No description provided for @torch.
  ///
  /// In en, this message translates to:
  /// **'Toggle torch'**
  String get torch;

  /// No description provided for @manualCode.
  ///
  /// In en, this message translates to:
  /// **'Ticket code'**
  String get manualCode;

  /// No description provided for @verify.
  ///
  /// In en, this message translates to:
  /// **'Verify ticket'**
  String get verify;

  /// No description provided for @demoScans.
  ///
  /// In en, this message translates to:
  /// **'Demo scan scenarios'**
  String get demoScans;

  /// No description provided for @valid.
  ///
  /// In en, this message translates to:
  /// **'Valid ticket'**
  String get valid;

  /// No description provided for @invalid.
  ///
  /// In en, this message translates to:
  /// **'Invalid ticket'**
  String get invalid;

  /// No description provided for @refunded.
  ///
  /// In en, this message translates to:
  /// **'Refunded ticket'**
  String get refunded;

  /// No description provided for @checked_in.
  ///
  /// In en, this message translates to:
  /// **'Already used'**
  String get checked_in;

  /// No description provided for @wrong_event.
  ///
  /// In en, this message translates to:
  /// **'Ticket for another event'**
  String get wrong_event;

  /// No description provided for @campaign_qr.
  ///
  /// In en, this message translates to:
  /// **'Campaign QR · no admission'**
  String get campaign_qr;

  /// No description provided for @verification.
  ///
  /// In en, this message translates to:
  /// **'Verification result'**
  String get verification;

  /// No description provided for @checkIn.
  ///
  /// In en, this message translates to:
  /// **'Check in'**
  String get checkIn;

  /// No description provided for @admitted.
  ///
  /// In en, this message translates to:
  /// **'Check-in recorded'**
  String get admitted;

  /// No description provided for @scanNext.
  ///
  /// In en, this message translates to:
  /// **'Scan next ticket'**
  String get scanNext;

  /// No description provided for @undo.
  ///
  /// In en, this message translates to:
  /// **'Undo check-in'**
  String get undo;

  /// No description provided for @undoTitle.
  ///
  /// In en, this message translates to:
  /// **'Undo this check-in?'**
  String get undoTitle;

  /// No description provided for @undoHint.
  ///
  /// In en, this message translates to:
  /// **'The ticket will become available for admission again.'**
  String get undoHint;

  /// No description provided for @undoDone.
  ///
  /// In en, this message translates to:
  /// **'Check-in reversed'**
  String get undoDone;

  /// No description provided for @confirm.
  ///
  /// In en, this message translates to:
  /// **'Confirm'**
  String get confirm;

  /// No description provided for @cancel.
  ///
  /// In en, this message translates to:
  /// **'Cancel'**
  String get cancel;

  /// No description provided for @attendees.
  ///
  /// In en, this message translates to:
  /// **'Attendees'**
  String get attendees;

  /// No description provided for @searchHint.
  ///
  /// In en, this message translates to:
  /// **'Name, email or ticket ID'**
  String get searchHint;

  /// No description provided for @search.
  ///
  /// In en, this message translates to:
  /// **'Search'**
  String get search;

  /// No description provided for @noResults.
  ///
  /// In en, this message translates to:
  /// **'No attendees found.'**
  String get noResults;

  /// No description provided for @loadMore.
  ///
  /// In en, this message translates to:
  /// **'Load more'**
  String get loadMore;

  /// No description provided for @ticket.
  ///
  /// In en, this message translates to:
  /// **'Ticket'**
  String get ticket;

  /// No description provided for @ticketType.
  ///
  /// In en, this message translates to:
  /// **'Ticket type'**
  String get ticketType;

  /// No description provided for @seat.
  ///
  /// In en, this message translates to:
  /// **'Section / row / seat'**
  String get seat;

  /// No description provided for @generalAdmission.
  ///
  /// In en, this message translates to:
  /// **'General admission'**
  String get generalAdmission;

  /// No description provided for @checkInTime.
  ///
  /// In en, this message translates to:
  /// **'Check-in time'**
  String get checkInTime;

  /// No description provided for @offline.
  ///
  /// In en, this message translates to:
  /// **'No connection. Admission requires an online response.'**
  String get offline;

  /// No description provided for @serverError.
  ///
  /// In en, this message translates to:
  /// **'Service unavailable. Please try again.'**
  String get serverError;

  /// No description provided for @unauthorized.
  ///
  /// In en, this message translates to:
  /// **'Your session expired. Please sign in again.'**
  String get unauthorized;

  /// No description provided for @forbidden.
  ///
  /// In en, this message translates to:
  /// **'You do not have permission for this action.'**
  String get forbidden;

  /// No description provided for @notFound.
  ///
  /// In en, this message translates to:
  /// **'This record is unavailable.'**
  String get notFound;

  /// No description provided for @conflict.
  ///
  /// In en, this message translates to:
  /// **'Ticket status changed. Refresh before trying again.'**
  String get conflict;

  /// No description provided for @badCredentials.
  ///
  /// In en, this message translates to:
  /// **'Incorrect email or password.'**
  String get badCredentials;

  /// No description provided for @storageError.
  ///
  /// In en, this message translates to:
  /// **'Unable to access your saved session.'**
  String get storageError;

  /// No description provided for @demoControls.
  ///
  /// In en, this message translates to:
  /// **'Demo controls'**
  String get demoControls;

  /// No description provided for @normal.
  ///
  /// In en, this message translates to:
  /// **'Normal connection'**
  String get normal;

  /// No description provided for @offlineMode.
  ///
  /// In en, this message translates to:
  /// **'Simulate offline'**
  String get offlineMode;

  /// No description provided for @serverMode.
  ///
  /// In en, this message translates to:
  /// **'Simulate server error'**
  String get serverMode;

  /// No description provided for @emptyAssignments.
  ///
  /// In en, this message translates to:
  /// **'Show no assignments'**
  String get emptyAssignments;

  /// No description provided for @revokeAssignment.
  ///
  /// In en, this message translates to:
  /// **'Revoke event access'**
  String get revokeAssignment;

  /// No description provided for @expireSession.
  ///
  /// In en, this message translates to:
  /// **'Expire session'**
  String get expireSession;

  /// No description provided for @resetDemo.
  ///
  /// In en, this message translates to:
  /// **'Reset demo data'**
  String get resetDemo;

  /// No description provided for @demoReset.
  ///
  /// In en, this message translates to:
  /// **'Demo records reset.'**
  String get demoReset;

  /// No description provided for @permissionDenied.
  ///
  /// In en, this message translates to:
  /// **'Undo not permitted'**
  String get permissionDenied;

  /// No description provided for @eventAdmin.
  ///
  /// In en, this message translates to:
  /// **'Event administrator'**
  String get eventAdmin;

  /// No description provided for @noAdmission.
  ///
  /// In en, this message translates to:
  /// **'This ticket cannot be admitted.'**
  String get noAdmission;

  /// No description provided for @resetHint.
  ///
  /// In en, this message translates to:
  /// **'Enter the email used for your staff account.'**
  String get resetHint;

  /// No description provided for @attendeeCount.
  ///
  /// In en, this message translates to:
  /// **'{count, plural, =0{No attendees} one{1 attendee} other{{count} attendees}}'**
  String attendeeCount(int count);

  /// No description provided for @cancelEventDemo.
  ///
  /// In en, this message translates to:
  /// **'Simulate event cancellation'**
  String get cancelEventDemo;

  /// No description provided for @demoShort.
  ///
  /// In en, this message translates to:
  /// **'Demo'**
  String get demoShort;

  /// No description provided for @overviewTab.
  ///
  /// In en, this message translates to:
  /// **'Overview'**
  String get overviewTab;

  /// No description provided for @scanTab.
  ///
  /// In en, this message translates to:
  /// **'Scan'**
  String get scanTab;

  /// No description provided for @guestsTab.
  ///
  /// In en, this message translates to:
  /// **'Guests'**
  String get guestsTab;

  /// No description provided for @welcomeTitle.
  ///
  /// In en, this message translates to:
  /// **'Welcome to\nyour next event.'**
  String get welcomeTitle;

  /// No description provided for @welcomeBody.
  ///
  /// In en, this message translates to:
  /// **'Sign in to check tickets and keep the door moving.'**
  String get welcomeBody;

  /// No description provided for @yourEvents.
  ///
  /// In en, this message translates to:
  /// **'Your events'**
  String get yourEvents;

  /// No description provided for @chooseEvent.
  ///
  /// In en, this message translates to:
  /// **'Choose where you’re checking in today.'**
  String get chooseEvent;

  /// No description provided for @attendance.
  ///
  /// In en, this message translates to:
  /// **'Attendance'**
  String get attendance;

  /// No description provided for @admittedLabel.
  ///
  /// In en, this message translates to:
  /// **'Admitted'**
  String get admittedLabel;

  /// No description provided for @ofRegistered.
  ///
  /// In en, this message translates to:
  /// **'of {total} registered'**
  String ofRegistered(String total);

  /// No description provided for @readyToScan.
  ///
  /// In en, this message translates to:
  /// **'Ready for the next guest'**
  String get readyToScan;

  /// No description provided for @scanGuide.
  ///
  /// In en, this message translates to:
  /// **'Position the ticket QR code inside the frame.'**
  String get scanGuide;

  /// No description provided for @manualEntry.
  ///
  /// In en, this message translates to:
  /// **'Enter code manually'**
  String get manualEntry;

  /// No description provided for @demoChoose.
  ///
  /// In en, this message translates to:
  /// **'Try a demo ticket'**
  String get demoChoose;

  /// No description provided for @checkingTicket.
  ///
  /// In en, this message translates to:
  /// **'Checking ticket…'**
  String get checkingTicket;

  /// No description provided for @readyAdmission.
  ///
  /// In en, this message translates to:
  /// **'Ready to admit'**
  String get readyAdmission;

  /// No description provided for @admissionHint.
  ///
  /// In en, this message translates to:
  /// **'Confirm entry to mark this ticket as used.'**
  String get admissionHint;

  /// No description provided for @admittedHint.
  ///
  /// In en, this message translates to:
  /// **'Entry is recorded. You’re ready for the next guest.'**
  String get admittedHint;

  /// No description provided for @usedHint.
  ///
  /// In en, this message translates to:
  /// **'This ticket has already been checked in.'**
  String get usedHint;

  /// No description provided for @blockedHint.
  ///
  /// In en, this message translates to:
  /// **'Do not admit this ticket. Check the details or ask the event organizer.'**
  String get blockedHint;

  /// No description provided for @noGuestsHint.
  ///
  /// In en, this message translates to:
  /// **'Try another name, email or ticket ID.'**
  String get noGuestsHint;

  /// No description provided for @preferences.
  ///
  /// In en, this message translates to:
  /// **'Preferences'**
  String get preferences;

  /// No description provided for @demoToolsHint.
  ///
  /// In en, this message translates to:
  /// **'Test ticket states and connection issues.'**
  String get demoToolsHint;

  /// No description provided for @signedInAs.
  ///
  /// In en, this message translates to:
  /// **'Signed in as event staff'**
  String get signedInAs;

  /// No description provided for @eventDetails.
  ///
  /// In en, this message translates to:
  /// **'Event details'**
  String get eventDetails;

  /// No description provided for @allGuests.
  ///
  /// In en, this message translates to:
  /// **'All guests'**
  String get allGuests;

  /// No description provided for @notArrived.
  ///
  /// In en, this message translates to:
  /// **'Not arrived'**
  String get notArrived;

  /// No description provided for @logoutConfirm.
  ///
  /// In en, this message translates to:
  /// **'Log out of this account?'**
  String get logoutConfirm;

  /// No description provided for @logoutHint.
  ///
  /// In en, this message translates to:
  /// **'You’ll need to sign in again to check tickets.'**
  String get logoutHint;

  /// No description provided for @clearSearch.
  ///
  /// In en, this message translates to:
  /// **'Clear search'**
  String get clearSearch;

  /// No description provided for @demoLoginHint.
  ///
  /// In en, this message translates to:
  /// **'The demo account is filled in. Sign in to explore.'**
  String get demoLoginHint;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['en', 'kk', 'ru'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return AppLocalizationsEn();
    case 'kk':
      return AppLocalizationsKk();
    case 'ru':
      return AppLocalizationsRu();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
