# Mobile implementation plan

Status: planned; no screens implemented by this document.

## Goal and scope

Build a rough, navigable Flutter prototype of the **Event Admin / check-in staff app** using Forui + Riverpod + Dio. All backend requests run against local mock HTTP responses. Follow `Project_Description.pdf` v0.3, especially sections 2.3, 4.8, 4.14, 7, and UC4. Include Kazakh, Russian, and English localization.

The PDF assigns event creation, checkout, payments, organizer analytics, campaign management, and attendee ticket downloads to the web application. They do not need mobile screens. The mobile app needs assigned events, QR verification, attendee lookup, check-in, authorized reversal, and attendance totals. Support is an optional contextual extension: the current backend does not give Event Admins delegated support permissions.

This is a screen prototype with simulated server behavior, not a claim that backend authentication or admission endpoints already exist. Keep a visible “Demo data” indicator and provide reproducible demo scenarios.

## Keep the implementation simple

- Retain `core/` and flat `features/<feature>/` folders.
- Use ordinary Riverpod providers/controllers without code generation.
- Screens call a feature controller; controllers call the shared Dio directly.
- Small concrete models and `fromJson` methods only where useful.
- No repositories, use-case classes, domain/data/presentation layers, local database, response cache, background sync, or offline admissions.
- Persist only the authentication token using the existing secure storage setup. Keep locale selection and mock records in memory.
- UI, API parsing, and session logic stay identical between mock and future real requests. Replace the Dio transport, not every screen.

## Screens and navigation

| Screen | Content and actions | Required states |
| --- | --- | --- |
| Session startup | Restore saved token before opening protected screens | Loading; secure-storage error with retry; signed out; restored session |
| Sign in | Email, password, submit, password visibility, language selector, forgot-password link | Required/invalid email; empty password; submitting; invalid credentials; service unavailable |
| Password reset | Email input and request confirmation | Validation; submitting; generic confirmation that does not reveal whether an account exists |
| Assigned events | Only events assigned to the demo Event Admin; title, venue, date/time, status; refresh; select event | Loading; empty assignments; request failure/retry; expired session |
| Event overview | Event name, venue/address, event-local time and timezone; registered and checked-in totals; remaining attendees; scan/search actions | Loading; counts; refresh failure; assignment revoked; cancelled event |
| Scan ticket | Camera preview, scan guide, torch, manual-code fallback; choose another event | Camera permission denied; no camera; verifying; offline/error; demo scenario selector |
| Verification result | Large icon + explicit status text; attendee, ticket type, event, optional section/row/seat; check-in action when permitted | Valid; invalid/tampered; wrong event; cancelled; refunded; already used; campaign QR rejected; network failure |
| Check-in confirmation | Successful admission, ticket holder, time; scan next; undo when allowed | Submitting; success; duplicate/conflict; permission denied; request failure |
| Attendee search | Search by name/email/ticket ID; server-style search and pagination; status filter if needed | Empty query; loading; results; no results; request failure |
| Attendee detail | Name, ticket type/ID, status, optional seat, check-in time; check in or undo based on permissions | Available admission; already checked in; cancelled/refunded; missing ticket; permission denied |
| Undo confirmation | Confirm accidental admission reversal, then show updated status/totals | Confirm/cancel; submitting; success; permission/conflict failure |
| Settings | Language, demo-mode label, account summary, logout | Locale changes immediately; logout clears token; storage error surfaced |

Navigation: startup → sign in → assigned events → event overview → scanner/result or attendee search/detail. Settings is accessible from the event list and event overview. Use simple Navigator pushes; no routing framework needed. After logout or token invalidation, remove protected routes so Back cannot reopen attendee information. Changing events clears the current scan and search state.

Registration/email-verification screens are not needed for the first staff prototype: staff use an existing assigned account. Their public account flows remain on web unless a mobile requirement is added.

## Scanner behavior

1. Select an assigned, non-cancelled event before scanning.
2. Provide a demo-code picker so every flow works without a camera. Add actual camera scanning with a small scanner package when wiring the screen; use platform permission descriptions.
3. Pause capture after the first code; allow one verification request at a time.
4. Send the raw opaque code and selected event ID to the mock admission endpoint. Never treat QR contents or a decoded ticket ID alone as proof of validity.
5. Display a verification result. A valid result allows an explicit **Check in** action; successful admission is shown only after that mutation succeeds.
6. The mock admission service must recheck the ticket on mutation. Two submissions cannot create two admissions; the second returns a duplicate conflict.
7. Update attendance totals and attendee state from the simulated server response or a new GET, not an unconditional local increment.
8. Resume camera scanning only after “Scan next.” Avoid automatic retries of check-in/undo POSTs.
9. Campaign links are always rejected for admission, regardless of whether they name the correct event. Never open a scanned campaign link automatically.
10. Online-only behavior: a simulated offline error blocks verification and admission. No queue for later upload.

## Mock request/response design

Implement one small mock `HttpClientAdapter` on the shared Dio. It dispatches by method/path/query, returns JSON/status codes, and uses in-memory fixtures for mutations. Use a flag such as `--dart-define=USE_MOCK_API=true`, defaulting to true for this prototype. Reuse the existing bearer/session interceptor.

- Simulate a short delay (about 300–600 ms).
- Recognize demo bearer tokens and reject expired ones with `401`.
- Restore a saved demo token across restarts without requiring login again; fixture business data resets on a fresh process.
- Enforce event assignments in mock GETs and mutations, including direct navigation/request attempts.
- Use UUID-shaped IDs, snake_case JSON, ISO-8601 timestamps with offsets, and existing backend enum values.
- Mirror FastAPI errors: `{"detail":"..."}` for ordinary errors; support field-error lists for `422`.
- Put proposed paths in one feature API file so future integration can change them easily.
- Do not enable real mode by quietly falling back to demo success when an endpoint is unavailable.

### Existing backend contracts: preserve exactly

The base prefix is `/api/v1`. Sources: `backend/features/events/{routes,schemas}.py`, `venues/schemas.py`, and `support/{routes,schemas,guards}.py`.

| Existing route | Shape and mobile handling |
| --- | --- |
| `GET /events` | Returns a raw `EventResponse[]`, not `{items: [...]}`. Current filters are `organizer_id` and `status`; **there is no assigned-staff filter or authorization yet**. The mock returns only the demo staff member's assigned events, clearly documented as proposed access behavior. Real integration must enforce assignments server-side. |
| `GET /events/detail?event_id=<uuid>` | Returns one `EventResponse`; keep the query parameter rather than inventing `/events/<id>`. |
| `GET /support/cases?limit=50&offset=0` | Returns a raw case array visible to the current user. |
| `POST /support/cases` | Body: `target`, optional `event_id`, `category`, `subject`, `message`. No order/ticket fields exist yet. |
| `GET /support/cases/detail?case_id=<uuid>` | Returns one case. |
| `GET /support/messages?case_id=<uuid>&limit=50&offset=0` | Returns messages oldest first. |
| `POST /support/messages?case_id=<uuid>` | Body: `{"body":"..."}`; author comes from the authenticated user. |
| `PATCH /support/cases/status?case_id=<uuid>` | Body: `{"status":"in_progress"}`; staff permission required. |
| `POST /support/cases/assign?case_id=<uuid>` | Assigns the case to the authenticated authorized staff member. |

`EventResponse` fields: `id`, `organizer_id`, `title`, `description`, `category`, `venue_id`, `start_time`, `end_time`, `timezone`, `capacity`, `visibility`, `is_assigned_seating`, `registration_start_time`, `registration_end_time`, `cover_image_url`, `status`, `venue`, `created_at`, `updated_at`. `venue` contains `id`, `name`, `address`, `created_at`, `updated_at`. Do not add attendance totals to this existing response; use the proposed summary request below.

### Proposed mock-only contracts: backend implementation pending

These are explicit prototype decisions, not existing backend routes. Confirm them with the backend owner before connecting real mode.

| Proposed route | Request | Mock response |
| --- | --- | --- |
| `POST /auth/login` | `{email, password}` | `{access_token, token_type: "bearer"}`; invalid credentials → `401` |
| `POST /auth/password-reset` | `{email}` | Generic success message |
| `GET /auth/me` | Bearer token | `{id, email, full_name, role}` using existing User field names; inactive/unassigned account handling |
| `GET /check-in/summary?event_id=...` | Assigned event ID | `{event_id, registered, checked_in}` |
| `GET /check-in/attendees?event_id=...&q=...&limit=...&offset=...` | Search and pagination | `{items: [...], total, limit, offset}`; this envelope is proposed only for this new route |
| `POST /check-in/verify` | `{event_id, qr_code}` | `{result, ticket, can_check_in, can_undo}`; no admission mutation |
| `POST /check-in/admit` | `{event_id, ticket_id}` | `{ticket, summary}`; revalidate state and permission; duplicate → `409` |
| `POST /check-in/undo` | `{event_id, ticket_id}` | `{ticket, summary}`; unauthorized → `403`; no active check-in → `409` |

Proposed ticket DTO: `{id, event_id, attendee_name, attendee_email, ticket_type_name, status, checked_in_at, section, row, seat}`. Optional seat fields may be null. Status values follow the PDF: `valid`, `checked_in`, `cancelled`, `refunded`. Verification-only `result` can additionally be `invalid`, `wrong_event`, or `campaign_qr`. Never persist raw scanned codes or passwords.

Current gaps: auth routes, staff assignments, issued tickets, admission QR format, check-in/undo, totals, and attendee lookup do not exist in this checkout. Existing event lists are not sufficient to safely replace assigned-event access. Support currently returns `503` until authentication is integrated, and its access rules authorize requesters/event owners/platform admins rather than delegated Event Admins.

## Demo fixtures and scenarios

Use fictional people and events only. Include two assigned events (one active, one upcoming), a cancelled assigned event, and a fourth unassigned event excluded from the staff list. Include mixed-language titles and an event with optional seat details to check layouts.

Provide deterministic demo codes for:

- Valid ticket, then already-used on a second admission.
- Already checked-in ticket with an authorized undo action.
- Valid ticket for another event.
- Cancelled and refunded tickets.
- Malformed/tampered code and a campaign HTTPS link.
- Ticket with section/row/seat and one without.
- Forbidden reversal, revoked assignment, and expired token.
- Offline failure, server error, empty assignment list, and empty search results.

The fake server owns its records and derives totals from them. Mutations update search results, ticket detail, and summary consistently. Demo controls should stay in a clearly labelled demo panel rather than cluttering the main admission flow.

## Localization

Use Flutter's built-in `gen-l10n` with ARB files and `flutter_localizations`; no extra localization framework.

- Files: `lib/l10n/app_kk.arb`, `app_ru.arb`, `app_en.arb`, plus `l10n.yaml`.
- Support `kk`, `ru`, `en`; use the device locale when supported and Kazakh as fallback. Offer language selection before and after login.
- Add generated app delegates alongside Forui localization delegates. Ensure controls, dialogs, validation, errors, scanner permission explanations, demo labels, and accessibility labels use translated strings.
- Keep the same keys/placeholders across all three files. Use ICU plurals for attendee counts.
- Translate server status/error codes through a mapping. Keep server enum values stable; never send translated labels in request bodies.
- Format numbers and dates for the selected locale. Show event-local time with the event timezone, independently of the device locale/timezone; use a small timezone helper/package if needed rather than assuming every event uses the device offset.
- Do not translate attendee names, event content, ticket IDs, or raw user messages.
- No saved locale preference in the first pass, matching the token-only persistence constraint.

## Optional support screens

After the admission flow works, add a rough case list → conversation → new contextual request flow only for roles allowed by the existing support contract. Use category `check_in` where relevant. No WebSockets, attachments, typing indicators, or background polling required; manual refresh is enough for the prototype.

Case statuses: `open`, `in_progress`, `waiting_for_customer`, `resolved`. Case fields: `id`, `requester_id`, `event_id`, `assignee_id`, `target`, `category`, `subject`, `status`, `created_at`, `updated_at`. Message fields: `id`, `case_id`, `author_id`, `body`, `created_at`.

For the Event Admin demo account, hide support management unless mock permissions explicitly model a future delegation. Do not imply the backend currently grants that access. Order/ticket context and support notifications remain backend gaps, not silently invented fields on current routes.

## Suggested files

```text
lib/
  app.dart
  main.dart
  l10n/                         # ARB + generated localization output
  core/
    network/api_client.dart
    network/mock_api_adapter.dart
    network/mock_fixtures.dart
    storage/token_storage.dart
    localization/locale_provider.dart
    widgets/request_state.dart  # Only if loading/error UI repeats
  features/
    auth/                       # Existing session + sign in/reset/account
    events/                     # Assigned list + overview + summary
    check_in/                   # Scanner/result/admission/undo + ticket model
    attendees/                  # Search + detail
    settings/                   # Language, demo controls, logout
    support/                    # Optional; existing permission rules
```

Keep each feature folder flat. Add a controller/model file when a screen actually needs it; do not create empty scaffolding for future layers.

## Delivery order

1. **Localization and shell:** ARB generation, three locales, Forui theme, language picker, navigation and demo indicator.
2. **Mock transport and authentication:** fixtures, login/reset/me, secure token restoration, logout/401 route reset.
3. **Assigned events:** list, event overview, summary and access/empty/error states.
4. **Admission:** demo scanning, result variants, server-style admission mutation, duplicate protection, confirmation and undo.
5. **Attendees:** search/pagination, detail, shared check-in/undo actions; refresh affected screens after mutations.
6. **Camera and rough mobile polish:** scanner plugin/platform permissions, safe areas, keyboard scrolling, readable result labels, usable tap targets. Keep demo scanning usable on simulators.
7. **Optional support:** only after the required staff flow and localization work; preserve backend roles/contracts.
8. **Verification and handoff:** tests, simulator walkthrough, requirements checklist, mock scenario instructions, and explicit real-API gaps.

## Completion checks

- Entire assigned-event → scan → admit → duplicate rejection → authorized undo flow works with mock HTTP and updates attendance totals.
- Manual lookup can admit the same ticket; scanner and manual entry share one ticket state.
- Unassigned/revoked events cannot be accessed by changing a route or request parameter.
- Campaign, wrong-event, cancelled, refunded, and malformed QR codes never show successful admission.
- Requests cannot check anyone in while offline; retry does not blindly repeat a mutation.
- Token restoration survives restart; `401` and logout remove protected routes; `403` and network/server errors preserve the session.
- All visible static strings and accessibility labels work in Kazakh, Russian, and English, including longer translations and plural counts.
- A small-screen walkthrough covers scrolling, keyboard overlap, loading/empty/error states, permission denial, and double taps.
- Meaningful tests cover mock contract parsing, mutation consistency, permission/duplicate failures, session lifecycle, navigation after logout, and locale switching.
- `flutter analyze` and `flutter test` pass. Camera/Keychain/Keystore behavior is explicitly device-tested or recorded as unverified.
- README clearly states which endpoints are mocked and which contracts still need backend agreement; no demo result is presented as live server verification.
