# Biletflow Staff

Flutter 3.44.4 / Dart 3.12.2. UI: [Forui](https://forui.dev/docs), state: Riverpod, HTTP: Dio. The only persisted app data is the authentication token, stored with `flutter_secure_storage` (Keychain on iOS, encrypted storage on Android).

## Run

### Real mode (against the backend)

```sh
flutter pub get
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000/api/v1/
```

The default API URL in debug builds is `http://localhost:8000/api/v1/`. For the Android emulator, pass `http://10.0.2.2:8000/api/v1/`. A physical device needs a reachable server address. HTTP cleartext traffic is enabled only in Android debug builds; release builds require an HTTPS `API_BASE_URL`. On iOS, use HTTPS or a local development hostname permitted by ATS.

Run the API and its dependencies from the repository root with `docker compose up -d backend`. Apply database migrations with `docker compose exec backend alembic upgrade head`.

### Demo mode (offline mock transport)

```sh
flutter run --dart-define=USE_MOCK_API=true
```

Demo mode uses `MockApiAdapter` with the same JSON shapes and routes as the backend. Demo event dates are generated relative to the current date.

## Features and API contract

Both real mode and demo mode expose the full door workflow:

- **Authentication**: `POST auth/login`, `POST auth/forgot-password`, `GET auth/me`.
- **Assigned events**: `GET checkin/events` (paginated). Events are sorted client-side with active and upcoming events first (earliest start time first), followed by completed events (most recent first).
- **Attendance totals**: `GET checkin/summary?event_id=...`. Counts (`registered`, `checked_in`, remaining) are always server-derived and refreshed after check-in, undo, or pull to refresh.
- **QR scanning & manual entry**: `GET tickets/verify?event_id=...&qr_token=...`, `POST tickets/check-in`, `POST tickets/undo-check-in`. Manual entry accepts either a 64-character QR token (verified via `tickets/verify`) or a ticket UUID (resolved via `checkin/attendees`). Campaign QR links are blocked client-side.
- **Guests search & detail**: `GET checkin/attendees?event_id=...&q=...&limit=20&offset=...`.
  - Returns a bare JSON array of `EventAttendeeResponse` rows (`ticket_id`, `order_id`, `attendee_name`, `attendee_email`, `ticket_type_id`, `ticket_type_name`, `ticket_status`, `order_status`, `checked_in_at`, `section`, `row`, `seat`, `created_at`).
  - Uses page-length pagination: requests 20 rows at a time, shows **Load more** while a full page of 20 rows is returned, and stops on a short page.
  - Tapping a guest renders the tapped row in `TicketScreen`; refresh and post-check-in/undo reloads query `GET checkin/attendees?event_id=...&q=<ticket_id>` (no separate detail route is called).
- **Assigned seats**: Verification (`TicketResponse`) and attendee rows (`EventAttendeeResponse`) expose nullable `section`, `row`, and `seat` fields. `TicketScreen` renders `<section> / <row> / <seat>` for assigned-seating tickets and falls back to **General admission** (localized in EN/KK/RU) when all three are null.

## Keep it simple

```text
lib/
  main.dart                           # ProviderScope + startup
  app.dart                            # Forui theme/localization + auth gate
  core/
    localization/locale_provider.dart # Locale state, date formatting, status labels
    network/api_client.dart           # Configured Dio + bearer/401 + HTTPS release guard
    network/mock_api_adapter.dart     # Backend-shaped mock transport + useMockApiProvider
    network/mock_fixtures.dart        # Demo events and tickets
    storage/token_storage.dart        # One secure token key
    theme/app_theme.dart              # Light/dark Forui + Material themes
    widgets/app_page.dart             # Shared page scaffold, error mapping, cards
  features/
    auth/                             # Session controller, auth gate, login screen
    events/                           # Event model, providers/sorting, list & overview
    attendees/                        # Guest search and page-length pagination
    check_in/                         # Scanner, ticket verification/detail, controller
    settings/                         # Account info, language, demo tools, logout
```

Keep each feature flat: its screen, controller/provider, and models/API functions only when needed. Screens watch Riverpod state. Controllers make requests directly with `ref.read(dioProvider)`. No repository interfaces, use cases, domain/data/presentation layers, generated providers, database, HTTP cache, or background refresh logic.

## Authentication integration

Sign-in sends `email` and `password` to `POST auth/login` and stores the returned `access_token`. Login and password reset explicitly opt out of session handling.

- Startup restores the token before rendering protected UI or sending authenticated requests. It does not require a network check or a new login.
- Requests to this API automatically include `Authorization: Bearer <token>`. Use relative API paths such as `checkin/events`; tokens are not attached to other hosts/paths.
- An authenticated `401` deletes the token and returns to the signed-out screen. A late response from an older token cannot clear a newer session.
- Public request failures, `403`, server failures, and offline/timeouts do not log the user out.
- `await ref.read(sessionProvider.notifier).logout()` clears secure storage and in-memory state. Storage failures surface as an error instead of silently claiming success.
- The backend decides token validity. There is no assumed JWT format, arbitrary client expiration timer, token refresh, or response caching.

## Release builds

- **Application / Bundle ID**: `kz.biletflow.staff` (Android `applicationId` & `namespace`, iOS `PRODUCT_BUNDLE_IDENTIFIER`).
- **App icons**: Brand launcher icon masters live in `assets/branding/app_icon.png` (1024×1024) and `assets/branding/app_icon_foreground.png`. All Android mipmap densities, Android adaptive icon layers (`mipmap-anydpi-v26/ic_launcher*.xml`, `drawable-*/ic_launcher_foreground.png`, `values/ic_launcher_background.xml`), and iOS `AppIcon.appiconset` sizes are generated from these masters.
- **HTTPS requirement**: Release builds enforce an `https://` `API_BASE_URL` at startup; passing an HTTP URL or omitting `API_BASE_URL` in release mode throws a `StateError`. Android release builds disable cleartext HTTP and app backups (`android:allowBackup="false"`).
- **Android release signing**: Generate or retrieve the upload keystore (`.jks`) from the team secret vault (never commit keystores or passwords to git):

```sh
keytool -genkeypair -v \
  -keystore ~/.android/biletflow-staff-upload.jks \
  -storetype PKCS12 -keyalg RSA -keysize 2048 -validity 10000 \
  -alias biletflow-upload
```

Copy `android/key.properties.example` to `android/key.properties` (git-ignored) and fill in the credentials:

```properties
storePassword=<keystore-password>
keyPassword=<key-password>
keyAlias=biletflow-upload
storeFile=/absolute/path/to/biletflow-staff-upload.jks
```

Build commands (targeting the production HTTPS API):

```sh
flutter build apk --release --dart-define=API_BASE_URL=https://35-228-54-76.sslip.io/api/v1/
flutter build appbundle --release --dart-define=API_BASE_URL=https://35-228-54-76.sslip.io/api/v1/
flutter build ipa --release --dart-define=API_BASE_URL=https://35-228-54-76.sslip.io/api/v1/
```

For iOS device distribution, sign in with the Apple Developer account in Xcode (`ios/Runner.xcworkspace`), ensure `kz.biletflow.staff` has Keychain Sharing enabled on the signing team, and generate/download the provisioning profile. Keychain entitlements are configured in `ios/Runner/Runner.entitlements`.

## Verify

```sh
flutter analyze
flutter test
flutter test --dart-define=USE_MOCK_API=true
```

Tests are self-contained and require no compile-time flag. They cover real-mode transport paths (backend attendee row parsing, attendance summary, attendee detail via search without removed routes, check-in, undo, 401 invalidation), mock scenarios, session persistence/race handling, error mapping across `kk`/`ru`/`en`, HTTPS release enforcement, event sorting, and narrow-screen/large-text layout.

### Device verification notes

Automated widget and transport checks pass in CI (`mobile` job in `.github/workflows/ci.yml`), including narrow width (320px), 1.4x text scale, real-mode guest search/detail, and all three locales. Physical hardware checks require a signed iOS device and Android device/emulator before release sign-off:

- [ ] Camera permission granted and denied states (verify fallback to manual entry)
- [ ] Torch toggle and app background/resume camera lifecycle
- [ ] Scanning a printed grayscale admission QR ticket
- [ ] Auth token survives cold app restart in Keychain/Keystore and logout clears it
- [ ] Dark mode, dynamic large text, and narrow viewport visual check on device
- [ ] Live attendee search, detail, check-in, and undo against an HTTPS backend
