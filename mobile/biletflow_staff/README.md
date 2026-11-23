# Biletflow Staff

Flutter 3.44.4 / Dart 3.12.2. UI: [Forui](https://forui.dev/docs), state: Riverpod, HTTP: Dio. The only persisted app data is the authentication token, stored with `flutter_secure_storage` (Keychain on iOS, encrypted storage on Android).

## Run

```sh
flutter pub get
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000/api/v1/
```

The default API URL is `http://localhost:8000/api/v1/`. For the Android emulator, pass `http://10.0.2.2:8000/api/v1/`. A physical device needs a reachable server address. HTTP is enabled only in Android debug builds; use HTTPS for production. On iOS, use HTTPS or a local development hostname permitted by ATS.

Run the API and its dependencies from the repository root with `docker compose up -d backend`. Apply database migrations with `docker compose exec backend alembic upgrade head`.

To run the demo without a server, use `flutter run --dart-define=USE_MOCK_API=true`. Guest search and attendance totals are available in demo mode until the staff API exposes those endpoints.

## Keep it simple

```text
lib/
  main.dart                         # ProviderScope + startup
  app.dart                          # Forui theme/localization + auth gate
  core/
    network/api_client.dart         # One configured Dio + bearer/401 handling
    storage/token_storage.dart      # One secure token key
  features/
    auth/
      session_controller.dart       # Restore/save/clear session
      auth_gate.dart                # Loading, error, signed out, signed in
    home/home_screen.dart
```

Keep each feature flat: its screen, controller/provider, and models/API functions only when needed. Screens watch Riverpod state. Controllers make requests directly with `ref.read(dioProvider)`. No repository interfaces, use cases, domain/data/presentation layers, generated providers, database, HTTP cache, or background refresh logic.

## Authentication integration

Sign-in sends `email` and `password` to `POST auth/login` and stores the returned `access_token`. Login and password reset explicitly opt out of session handling.

- Startup restores the token before rendering protected UI or sending authenticated requests. It does not require a network check or a new login.
- Requests to this API automatically include `Authorization: Bearer <token>`. Use relative API paths such as `events`; tokens are not attached to other hosts/paths.
- An authenticated `401` deletes the token and returns to the signed-out screen. A late response from an older token cannot clear a newer session.
- Public request failures, `403`, server failures, and offline/timeouts do not log the user out.
- `await ref.read(sessionProvider.notifier).logout()` clears secure storage and in-memory state. Storage failures surface as an error instead of silently claiming success.
- The backend decides token validity. There is no assumed JWT format, arbitrary client expiration timer, token refresh, or response caching.

Android release builds have Internet permission and disable app backups to avoid restoring encrypted tokens without their keys. iOS Runner configurations include Keychain entitlements; configure your own bundle ID and signing team for device builds.

## Verify

```sh
flutter analyze
flutter test --dart-define=USE_MOCK_API=true
```

Tests cover restoring sessions, logout, bearer headers, `401` invalidation, public requests, external URLs, network/server failures, and overlapping login/logout or stale responses. Platform Keychain/Keystore behavior still needs a signed-device smoke test.
