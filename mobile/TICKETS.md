# Mobile completion tickets

Scope: the Event Admin app against the SRS (§4.8, the mobile clause in §4.14,
and the app requirements in §7) and the backend on `main` at `75785ce`.

These tickets assume the backend stays as it is. No backend change is required
to close MOB-01 through MOB-11. MOB-12 is the only blocked one.

Definition of done for the mobile side:

- The app runs in real mode against the seeded backend and exposes every §4.8
  capability, including attendee search and attendance totals.
- Demo mode still works and uses the same JSON shapes as the backend.
- Tests cover both transports and do not need a compile-time flag.
- CI runs analyze and tests.
- A release build reaches the API over HTTPS.

## Order

| Ticket | Title | Priority | Size | Depends on |
| --- | --- | --- | --- | --- |
| MOB-01 | Connect Guests to real attendee search | P1 | M | none |
| MOB-02 | Enable attendance totals in real mode | P1 | S | none |
| MOB-03 | Replace the missing ticket-detail call | P1 | S | MOB-01 |
| MOB-04 | Align mock transport and fixtures with the backend | P1 | M | MOB-01, MOB-03 |
| MOB-05 | Make error states truthful | P2 | S | none |
| MOB-06 | Make tests self-contained and cover real mode | P2 | M | MOB-01 to MOB-04 |
| MOB-07 | Add the mobile job to CI | P2 | S | MOB-06 |
| MOB-08 | Update mobile documentation | P2 | S | MOB-01 to MOB-07 |
| MOB-09 | Clean up the cancelled-event demo | P3 | S | none |
| MOB-10 | Prepare release builds | P2 | M | none |
| MOB-11 | Verify camera, storage and accessibility on devices | P2 | M | MOB-10 |
| MOB-12 | Display assigned seats | P2 | S | backend seat data |
| MOB-13 | Small UX cleanup | P3 | S | none |

## MOB-01 - Connect Guests to real attendee search

Priority: P1
Size: M
Blocks: attendee search requirement in §4.8

Current behaviour:

- The Guests destination is only added when `useMockApi` is true
  (`lib/features/events/event_overview_screen.dart:50`).
- `AttendeesScreen` expects `{items, total, limit, offset}` and parses rows as
  `AdmissionTicket` (`lib/features/attendees/attendees_screen.dart:69-87`).
- The backend returns a bare `list[EventAttendeeResponse]`
  (`backend/features/checkin/routes.py:36`).
- The row fields differ: backend `ticket_id` and `ticket_status`, client `id`
  and `status` (`lib/features/check_in/ticket.dart:20-34`).

Scope:

- Remove the `useMockApi` gate on the Guests destination.
- Add a mapper from the backend row to the client model. Map `ticket_id`,
  `ticket_status`, `ticket_type_name`, `attendee_name`, `attendee_email`,
  `checked_in_at`. Leave seat fields null until MOB-12.
- Parse the raw list. Drop the `total` field from the UI. Paginate with the page
  length: request 20, show "Load more" while a full page is returned, stop on a
  short page.
- Keep the debounce, stale-response generation guard, pull to refresh, empty
  state and retry.
- Do not invent an exact filtered count. The overview totals come from the
  summary endpoint.

Acceptance criteria:

- Guests is visible in real mode.
- Search by name, email and full ticket UUID works.
- Paging returns no duplicates and stops at the end.
- Tapping a row opens detail through MOB-03.
- No type cast errors and no reliance on `total`.
- `flutter analyze` is clean.

Files: `event_overview_screen.dart`, `attendees_screen.dart`,
`check_in/ticket.dart`, `core/network/api_client.dart`.

## MOB-02 - Enable attendance totals in real mode

Priority: P1
Size: S
Blocks: registered and checked-in totals requirement in §4.8

Current behaviour:

- The attendance card is rendered only when `useMockApi` is true
  (`event_overview_screen.dart:113`).
- Summary invalidation after refresh and after admission/undo is also gated
  (`event_overview_screen.dart:60`, `check_in/check_in_controller.dart:42`).
- The endpoint exists: `GET /checkin/summary?event_id=...`
  (`backend/features/checkin/routes.py:61`).

Scope:

- Render the summary card in both modes.
- Invalidate `summaryProvider(eventId)` after check-in and undo in both modes.
- Keep server-derived counts. Do not increment locally.
- Keep loading, error and retry states.

Acceptance criteria:

- Real mode shows registered, checked in, remaining and the progress bar.
- Admit and undo update the numbers from the server response.
- A failed summary shows an error and retry, not zeroes.
- The screen refreshes on pull to refresh.

Files: `event_overview_screen.dart`, `check_in/check_in_controller.dart`.

## MOB-03 - Replace the missing ticket-detail call

Priority: P1
Size: S
Depends on: MOB-01

Current behaviour:

- The detail screen calls `GET checkin/tickets/detail`
  (`lib/features/check_in/ticket_screen.dart:73-81`). That route does not exist.
- `GET /tickets/detail` is limited to the order owner, event organizer or
  platform admin (`backend/features/tickets/routes.py:49`,
  `backend/features/orders/guards.py:26`), so an assigned Event Admin cannot use
  it either.

Scope:

- Preferred: pass the tapped attendee row into `TicketScreen` and render it.
  After a check-in or undo, reload the row with
  `GET /checkin/attendees?event_id=...&q=<ticket_id>`.
- Alternative: always load detail through that search endpoint and take the
  single matching row.
- Remove the call to `checkin/tickets/detail`.
- Keep the scanner path (`qrToken`) unchanged.
- Treat a missing row as not found, not as an invalid ticket.
- Keep refresh working from the detail screen.

Acceptance criteria:

- Tapping a guest opens detail in real mode.
- Check-in and undo work from the detail screen.
- Refresh shows the current server state.
- No request targets a route the backend does not expose.
- Scanner detail and attendee detail share one admission state.

Files: `ticket_screen.dart`, `attendees_screen.dart`, `check_in/ticket.dart`.

## MOB-04 - Align mock transport and fixtures with the backend

Priority: P1
Size: M
Depends on: MOB-01, MOB-03

Current behaviour:

- The mock returns the prototype envelope and a detail route the backend does
  not have (`lib/core/network/mock_api_adapter.dart:135-167`).
- Tests assert that shape (`test/mock_api_test.dart:180-202`). This is why the
  suite is green while real mode is broken.

Scope:

- Return a raw list from the mock `/checkin/attendees`, using
  `ticket_id`, `order_id`, `attendee_name`, `attendee_email`,
  `ticket_type_id`, `ticket_type_name`, `ticket_status`, `order_status`,
  `checked_in_at` and `created_at`.
- Remove the mock detail route when MOB-03 drops it.
- Keep mock events, verify, check-in, undo and summary aligned with the backend.
- Add contract tests that parse backend-shaped JSON for events, attendees,
  verify, check-in and summary.
- Replace tests that assert `total` with page-length behaviour.

Acceptance criteria:

- Every consumed mock route matches the backend field names and response shape.
- A renamed field breaks a test.
- No test depends on a route the backend does not expose.
- Demo mode still exercises valid, used, cancelled, refunded, campaign and
  duplicate scenarios.

Files: `mock_api_adapter.dart`, `mock_fixtures.dart`, `test/mock_api_test.dart`.

## MOB-05 - Make error states truthful

Priority: P2
Size: S

Current behaviour:

- Any non-Dio error shows "Unable to access your saved session"
  (`lib/core/widgets/app_page.dart:183-184`). A parse error therefore looks like
  a storage failure.
- A failed detail load still renders the red "Invalid ticket" headline
  (`ticket_screen.dart:32,165`).
- 422 maps to "This field is required" (`app_page.dart:219`).
- Order states such as `pending` and `invalid_order` fall through to the generic
  invalid label.

Scope:

- Add a generic fallback for non-Dio errors and keep the storage message for
  storage operations only.
- Add a load-error state to the detail screen. Show no status icon or status
  headline until data loads. Offer retry.
- Map 422 to a validation message, or use the server detail when it is a
  string.
- Give `invalid_order` and `pending` a specific reason, or map them to invalid
  intentionally.
- Keep the existing offline, 403, 404, 409 and cancelled/suspended mappings.

Acceptance criteria:

- A parse failure never claims the session is broken.
- A failed detail load never claims the ticket is invalid.
- Messages exist in Kazakh, Russian and English.
- Existing error-mapping tests still pass.

Files: `app_page.dart`, `ticket_screen.dart`, `locale_provider.dart`,
`l10n/app_*.arb`.

## MOB-06 - Make tests self-contained and cover real mode

Priority: P2
Size: M
Depends on: MOB-01 to MOB-04

Current behaviour:

- `useMockApi` is compile-time (`mock_api_adapter.dart:10`). Running
  `flutter test` without `--dart-define=USE_MOCK_API=true` fails 7 of 9 widget
  tests.
- No test covers the real transport or the backend attendee shape.

Scope:

- Remove the compile-time dependency from tests. Inject the mock choice through
  a provider override or a test-only adapter.
- Add tests for the real-mode paths: attendee list parsing, summary rendering,
  detail lookup, check-in, undo and 401 handling.
- Keep the mock scenario tests.
- Ensure `flutter test` passes with no extra flags, and that the demo flag also
  passes.

Acceptance criteria:

- `flutter test` passes as written.
- `flutter test --dart-define=USE_MOCK_API=true` passes.
- At least one test parses the backend attendee row shape.
- At least one test asserts the summary appears without mock mode.
- At least one test fails if the detail screen calls the removed route.

Files: `test/`, `core/network/`, `core/storage/`.

## MOB-07 - Add the mobile job to CI

Priority: P2
Size: S
Depends on: MOB-06

Current behaviour:

- `.github/workflows/ci.yml` runs backend, frontend and e2e only. Mobile is not
  checked.

Scope:

- Add a `mobile` job.
- Install Flutter and run `flutter pub get`, `flutter analyze` and
  `flutter test`.
- Cache the pub cache.
- Run on pull requests and pushes to `main`.
- Keep the job independent of the backend services.

Acceptance criteria:

- A failing analyze or test blocks the pull request.
- The job passes on `main`.
- Runtime stays under a few minutes.

Files: `.github/workflows/ci.yml`.

## MOB-08 - Update mobile documentation

Priority: P2
Size: S
Depends on: MOB-01 to MOB-07

Current behaviour:

- `mobile/biletflow_staff/README.md:16` says guest search and totals are demo
  only until the staff API exposes them. The API exists.
- The README does not describe the attendee contract or what real mode covers.

Scope:

- Document real-mode features and the endpoints used.
- Document the attendee row shape and the page-length pagination rule.
- Keep the demo-mode instructions and the test command accurate.
- Update `mobile/UI_REDESIGN.md` if Guests behaviour changes.
- Remove statements that no longer match the code.

Acceptance criteria:

- A new developer can run both modes using the README alone.
- No documented endpoint or flag contradicts the code.

Files: `mobile/biletflow_staff/README.md`, `mobile/UI_REDESIGN.md`.

## MOB-09 - Clean up the cancelled-event demo

Priority: P3
Size: S

Current behaviour:

- The demo toggle cancels the demo event
  (`lib/features/settings/settings_screen.dart:216-231`).
- `/checkin/events` filters cancelled events, so the event disappears and
  `eventProvider` resolves to a 404 (`event_providers.dart:36-50`). The overview
  shows a generic error instead of the cancelled state.
- The cancelled banner is unreachable in both modes.

Scope:

- Choose one:
  - remove the cancellation toggle and the dead cancelled branches, or
  - keep the event listed in the mock and let verification return the server
    400, so the blocked admission path is still demonstrated.
- Keep the server-side block. The backend still returns 400 for a cancelled
  event.

Acceptance criteria:

- No demo control turns the overview into a 404.
- The cancelled-event server response still shows "Admission closed".
- No unreachable cancelled-state code remains.

Files: `settings_screen.dart`, `event_overview_screen.dart`,
`mock_api_adapter.dart`.

## MOB-10 - Prepare release builds

Priority: P2
Size: M

Current behaviour:

- Android application ID is `com.example.biletflow_staff` and release uses the
  debug signing config (`android/app/build.gradle.kts:18-33`).
- The default API URL is `http://localhost:8000/api/v1/`
  (`lib/core/network/api_client.dart:10-13`).
- iOS uses the default bundle identifier.
- Launcher icons are the Flutter defaults.

Scope:

- Set a real Android application ID and iOS bundle identifier.
- Configure release signing and document where the keystore lives. Do not
  commit secrets.
- Require an HTTPS `API_BASE_URL` for release. Keep HTTP allowed only in the
  Android debug manifest.
- Set the app name and icons if the team has brand assets.
- Document release build commands.

Acceptance criteria:

- A release build installs on a device and reaches the API over HTTPS.
- Debug builds still reach a local HTTP backend.
- No `com.example` identifier ships.

Files: `android/app/build.gradle.kts`, `ios/Runner.xcodeproj`,
`android/app/src/main/AndroidManifest.xml`, `README.md`.

## MOB-11 - Verify camera, storage and accessibility on devices

Priority: P2
Size: M
Depends on: MOB-10

Current behaviour:

- The README says camera, Keychain/Keystore and release behaviour still need a
  signed-device smoke test.
- Only widget tests run today.

Scope:

- Test on one iOS device or simulator and one Android device or emulator:
  - camera permission granted and denied,
  - torch and app background/resume,
  - scanning a printed grayscale ticket,
  - token survives restart and logout clears it,
  - large text, narrow width and dark mode,
  - attendee search and detail in real mode.
- Record the result and any device-only defects.

Acceptance criteria:

- A short verification note exists in the README or the pull request.
- Defects are fixed or documented with a follow-up.
- No mock-only path is needed to complete the door flow.

Files: device test notes, `README.md`.

## MOB-12 - Display assigned seats

Priority: P2
Size: S
Blocked by: backend seat data (sections, rows, seats, ticket seat fields)

Current behaviour:

- The client reads `section`, `row` and `seat` from the ticket JSON
  (`lib/features/check_in/ticket.dart:28-30`).
- The backend never sends them. The `Ticket` model and `TicketResponse` have no
  seat fields, and there are no seat models at all.
- The seat row is displayed only in mock mode
  (`lib/features/check_in/ticket_screen.dart:307`).

Scope:

- Once the backend exposes the fields, map and display them in the verification
  result and attendee detail.
- Fall back to "General admission" when all three are null.
- Remove the `useMockApi` condition.
- Add tests for a seated ticket and a general-admission ticket.

Acceptance criteria:

- A seated ticket shows section, row and seat from the real API.
- A general-admission ticket shows "General admission".
- No mock-only gate remains.

Files: `check_in/ticket.dart`, `ticket_screen.dart`, `mock_api_adapter.dart`,
`mock_fixtures.dart`.

## MOB-13 - Small UX cleanup

Priority: P3
Size: S

Current behaviour:

- The settings avatar is hardcoded to "AD"
  (`lib/features/settings/settings_screen.dart:65`).
- Thirteen localization keys are unused.
- Events are listed by ascending start time, so completed events appear first.
- The mock event dates are in the past relative to the current demo date.
- Manual entry asks for a "ticket code" but expects the raw 64-hex token, which
  is not realistically typed by hand.

Scope:

- Derive avatar initials from the account name.
- Remove unused localization keys.
- Sort or group events with active and upcoming first, if the product wants it.
- Keep mock dates relative to the current date, or document that they are fixed.
- Clarify the manual-entry label, or accept the ticket UUID and look it up.

Acceptance criteria:

- No hardcoded account values.
- No unused localization keys.
- The event list ordering is intentional and documented.
- The manual-entry label matches what the field accepts.

Files: `settings_screen.dart`, `events_screen.dart`, `mock_fixtures.dart`,
`scanner_screen.dart`, `l10n/app_*.arb`.

## Out of scope

- Backend API changes. Everything above uses existing endpoints.
- Support screens. The mobile requirement does not include them, and delegated
  Event Admin support permissions do not exist on the backend.
- Offline check-in. The SRS explicitly defers it.
- Event creation, checkout, payments and organizer analytics. These stay on the
  web client.
- Seat map and seat holds. These are backend product work; MOB-12 covers only
  the mobile display after the data exists.
