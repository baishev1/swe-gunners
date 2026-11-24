# Mobile blocker tickets

Tickets tracking external or environment blockers that prevent closing the
remaining mobile items (`MOB-11`, `MOB-12`, and signed release distribution
from `MOB-10`) in `mobile/TICKETS.md`.

## Order

| Ticket | Title | Owner | Priority | Size | Unblocks | Status |
| --- | --- | --- | --- | --- | --- | --- |
| BLK-01 | Expose seat fields on tickets and attendee responses | Backend | P2 | M | MOB-12 | Done |
| BLK-02 | Provision Android release keystore and iOS signing team | Release / DevOps | P2 | S | MOB-10, MOB-11 | Partial (Android done; iOS portal profile pending) |
| BLK-03 | Provide brand app icons and adaptive assets | Design / Product | P3 | S | MOB-10 | Done |
| BLK-04 | Execute physical iOS and Android device smoke test | QA / Mobile | P2 | M | MOB-11 | Open (requires physical devices) |

## BLK-01 - Expose seat fields on tickets and attendee responses

Status: Done (also completed `MOB-12` on mobile)
Owner: Backend
Priority: P2
Size: M
Unblocks: `MOB-12` (Display assigned seats)

Current behaviour:

- `Event.is_assigned_seating` exists (`backend/features/events/models.py:22`),
  but `Ticket` (`backend/features/tickets/models.py:7-17`) has no seat columns
  and there are no venue section/row/seat models.
- `TicketResponse` and `EventAttendeeResponse`
  (`backend/features/tickets/schemas.py:8-37`) do not return `section`, `row`,
  or `seat`.
- As a result, `mobile/biletflow_staff/lib/features/check_in/ticket_screen.dart`
  hides the seat row whenever `ticket.seat == null`.

Scope:

- Add nullable `section`, `row`, and `seat` fields (or full seat models linked
  from `Ticket`) with an Alembic migration.
- Include nullable `section`, `row`, and `seat` strings in:
  - `TicketResponse` (`GET /tickets/verify`, `POST /tickets/check-in`,
    `POST /tickets/undo-check-in`), and
  - `EventAttendeeResponse` (`GET /checkin/attendees`,
    `GET /tickets/event-attendees`).
- Seed at least one assigned-seating event with seated tickets and one
  general-admission event with `null` seat fields in `backend/scripts/seed.py`.
- Add backend unit/integration tests covering both seated and general-admission
  tickets.

Acceptance criteria:

- Seated tickets return non-null `section`, `row`, and `seat` from both
  `GET /tickets/verify` and `GET /checkin/attendees`.
- General-admission tickets return `null` for `section`, `row`, and `seat`.
- Existing clients remain backward-compatible.
- `ruff`, `mypy`, and `pytest` pass.

Files: `backend/features/tickets/models.py`,
`backend/features/tickets/schemas.py`, `backend/features/checkin/routes.py`,
`backend/alembic/versions/`, `backend/scripts/seed.py`, `backend/tests/`.

## BLK-02 - Provision Android release keystore and iOS signing team

Status: Partial — Android upload keystore provisioned locally (outside git) and release APK verified via `apksigner` against `https://35-228-54-76.sslip.io/api/v1/`; iOS still requires Apple Developer portal sign-in and a provisioning profile for `kz.biletflow.staff` (team `4WXX2K4MM2`) with Keychain Sharing enabled.
Owner: Release / DevOps
Priority: P2
Size: S
Unblocks: `MOB-10` (signed release distribution), `MOB-11` (signed-device smoke test)

Current behaviour:

- `mobile/biletflow_staff/android/app/build.gradle.kts` reads
  `android/key.properties` when present and falls back to the debug signing
  config when absent.
- iOS bundle identifier is set to `kz.biletflow.staff`, but no Apple Developer
  `DEVELOPMENT_TEAM` or provisioning profile is configured.

Scope:

- Generate the Android upload keystore (`.jks`) and store it plus its
  credentials in the team secret vault (never in git).
- Document how release engineers create the git-ignored
  `mobile/biletflow_staff/android/key.properties` file.
- Register `kz.biletflow.staff` with Keychain Sharing capability in the Apple
  Developer portal and configure the signing team for TestFlight / ad-hoc
  device builds.
- Verify release builds target the production HTTPS API
  (`https://35-228-54-76.sslip.io/api/v1/`).

Acceptance criteria:

- `flutter build apk --release --dart-define=API_BASE_URL=https://35-228-54-76.sslip.io/api/v1/`
  produces a release-signed APK using the upload keystore (not debug keys).
- A signed iOS build installs on a physical test iPhone with Keychain access.
- No keystore files, passwords, or provisioning secrets are committed to git.

Files: `mobile/biletflow_staff/android/app/build.gradle.kts`,
`mobile/biletflow_staff/ios/Runner.xcodeproj/project.pbxproj`,
`mobile/biletflow_staff/README.md`.

## BLK-03 - Provide brand app icons and adaptive assets

Status: Done — 1024×1024 master icon and adaptive foreground added under `mobile/biletflow_staff/assets/branding/`, and all Android mipmaps, adaptive icon resources, iOS `AppIcon.appiconset` sizes, and macOS icons regenerated.
Owner: Design / Product
Priority: P3
Size: S
Unblocks: `MOB-10` (brand launcher icons)

Current behaviour:

- Android (`mobile/biletflow_staff/android/app/src/main/res/mipmap-*`) and iOS
  (`mobile/biletflow_staff/ios/Runner/Assets.xcassets/AppIcon.appiconset`) still
  use the default Flutter launcher icons.

Scope:

- Supply a 1024x1024 Biletflow Staff icon master asset and Android adaptive
  foreground/background layers.
- Regenerate all Android mipmap densities and iOS AppIcon asset catalog sizes.

Acceptance criteria:

- Installed Android and iOS builds display the Biletflow Staff icon on the home
  screen and app switcher.
- No default Flutter launcher icon assets remain.

Files: `mobile/biletflow_staff/android/app/src/main/res/`,
`mobile/biletflow_staff/ios/Runner/Assets.xcassets/AppIcon.appiconset/`.

## BLK-04 - Execute physical iOS and Android device smoke test

Status: Open — requires physical iOS and Android hardware (no physical devices connected) and iOS provisioning profile from `BLK-02`. All 45 automated Flutter tests pass.
Owner: QA / Mobile
Priority: P2
Size: M
Depends on: `BLK-02`
Unblocks: `MOB-11` (Verify camera, storage and accessibility on devices)

Current behaviour:

- All 44 automated widget and transport tests pass, including narrow width
  (320px), 1.4x text scale, EN/KK/RU localization, and real-mode API flows.
- Hardware-only behavior (camera permissions, torch, app lifecycle resume,
  printed grayscale QR scanning, Keychain/Keystore cold-restart persistence, and
  live HTTPS requests) cannot run in headless CI tests.

Scope:

- Install signed release builds pointed at
  `https://35-228-54-76.sslip.io/api/v1/` on one physical iOS device and one
  physical Android device.
- Execute every item in the **Device verification notes (`MOB-11`)** checklist
  in `mobile/biletflow_staff/README.md`:
  - camera permission granted and denied (confirm manual-entry fallback),
  - torch toggle and app background/resume camera recovery,
  - scanning a printed grayscale admission QR ticket,
  - auth token survives cold restart in Keychain/Keystore and logout clears it,
  - dark mode, dynamic large text, and narrow viewport rendering,
  - live attendee search, detail, check-in, and undo in real mode.
- Record device models, OS versions, date, and any defects found.

Acceptance criteria:

- Checklist in `mobile/biletflow_staff/README.md` is completed and signed off
  for both iOS and Android.
- Any device-only defects are fixed or tracked in follow-up tickets.

Files: `mobile/biletflow_staff/README.md`.
