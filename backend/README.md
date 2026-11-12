# BiletFlow API

FastAPI service backing the web client and the event admin mobile app.

## Setup

```bash
uv sync
cp .env.example .env
docker compose -f ../docker-compose.yml up -d postgres
uv run alembic upgrade head
uv run fastapi dev app/main.py
```

Leave `POSTGRES_SERVER` empty in `.env` to run against SQLite instead and skip the
container.

Verification and password reset emails go to `SMTP_HOST`. Start Mailpit with
`docker compose up -d mailpit` and read them at http://localhost:8025. With `SMTP_HOST`
empty the message is written to the log instead.

## Layout

```
app/
  main.py        FastAPI instance, CORS, router registration
  lifespan.py    startup and shutdown hooks
core/            true globals only: settings, database, logging, helpers
features/        one folder per domain area
alembic/         migrations, with automatic model discovery
tests/           pytest suite
```

`core/` holds nothing feature-specific. Anything that belongs to a single part of
the domain lives in `features/<name>/` — JWT signing and password hashing, for
example, belong to `features/auth/`, not to `core/`.

`core/settings.py` is the exception: it is the single configuration surface for
the whole app, so a feature's config keys (`JWT_SECRET` and friends) are declared
there. Keep it lean.

## Core

| Module          | Contents                                                        |
| --------------- | --------------------------------------------------------------- |
| `settings.py`   | `Settings` loaded from `.env`, exported as `settings`            |
| `database.py`   | `engine`, `init_db`, `get_db`, `DbBase`, `AwareDateTime`, `uuid7` |
| `logging.py`    | `init_logging`                                                   |
| `helpers.py`    | `time_now`                                                       |

`core/__init__.py` re-exports all of it and defines `init_core()`, which the
lifespan calls on startup.

`DbBase` gives every model a UUIDv7 primary key, timezone-aware `created_at` and
`updated_at`, and a snake_case `__tablename__` derived from the class name.

`settings.database_url` picks SQLite when `IS_DEV_ENV=true` and `POSTGRES_SERVER`
is empty; otherwise it builds a PostgreSQL URL from the `POSTGRES_*` variables.

## Request flow

```
HTTP request
  -> routes.py     APIRouter, request/response schemas, status codes
  -> service.py    business rules and transaction boundaries
  -> models.py     SQLAlchemy models on top of core.DbBase
```

## Feature folders

A feature owns its models, its persistence and its HTTP surface. The file names
are fixed:

```
features/<name>/
  __init__.py     from . import routes
  models.py       SQLAlchemy models, subclassing core.DbBase
  schemas.py      Pydantic request and response models
  dtos.py         internal data shapes passed between services (optional)
  routes.py       APIRouter with its own prefix and tags
  service.py      business rules, exported as a module-level singleton
  guards.py       dependencies that load an entity and reject if missing (optional)
  dependencies.py FastAPI dependencies specific to this feature (optional)
```

Rules:

- `core/` never imports from `features/`.
- A feature may import from `core` and from another feature's `service`, `models`,
  `schemas` or `guards`. It must not import another feature's `routes`.
- Routes stay thin: validate input, call the service, return a schema.
- Services are module-level singletons and take `db: Session` per call rather
  than holding one.
- `models.py` must live at exactly that path; Alembic discovery depends on it.

## Adding a feature

```bash
mkdir features/events
```

Create the files listed above, then register the router in `app/main.py`:

```python
from features import events

app.include_router(events.routes.router, prefix="/api/v1")
```

Every feature router is mounted under `/api/v1`. `/health` stays outside the prefix.

Finally generate a migration for the new models, as described under Migrations.

## Migrations

`alembic/env.py` imports every `features/*/models.py`, so autogenerate sees a
model as soon as it exists at that path. No manual import list to maintain.

```bash
uv run alembic revision --autogenerate -m "add events"
uv run alembic upgrade head
uv run alembic downgrade -1
```

Read the generated migration before applying it. Every schema change ships with one.
`core.UTCDateTime` columns render as `sa.DateTime()` so migrations never import
application code.

## Conventions

- Python 3.13, formatted and linted with Ruff, type-checked with mypy.
- Synchronous SQLAlchemy 2.0 sessions; FastAPI runs `def` endpoints in a threadpool.
- Money is stored in minor units as integers, never floats.
- Timestamps are timezone-aware and stored in UTC via `core.UTCDateTime`.
- Settings are read through `core.settings`, never from `os.environ` directly.
- Python modules and functions: `snake_case`. Classes: `PascalCase`.
- Database tables and columns: singular `snake_case`.

## Commands

```bash
uv run pytest
uv run ruff check . && uv run ruff format .
uv run mypy app core features tests
```

## Support (part 5)

The first support slice handles event-linked attendee cases and platform-support
cases for organizers. It uses REST requests; the client can poll for messages.

All routes are under `/api/v1/support`:

| Method | Route | Purpose |
| --- | --- | --- |
| POST | `/cases` | Create a case and its first message in one transaction |
| GET | `/cases` | List cases visible to the current user |
| GET | `/cases/detail?case_id=...` | Read a case |
| GET | `/messages?case_id=...` | Read messages, oldest first |
| POST | `/messages?case_id=...` | Reply to a case |
| PATCH | `/cases/status?case_id=...` | Staff change the case status |
| POST | `/cases/assign?case_id=...` | Staff assign the case to themselves |

Lists accept `limit` (1–100, default 50) and `offset` (default 0).
Create a case with `target` (`organizer` or `platform`), `category`, `subject`,
`message`, and optional `event_id`. Organizer-targeted cases require an event.
Statuses are `open`, `in_progress`, `waiting_for_customer`, and `resolved`.

Requesters can read/reply to their own cases. Event owners and assigned staff with
`can_manage_support=true` can handle cases targeting their event's organizer.
Users with role `platform_admin` can handle
all cases, including organizer requests to the platform. Other users receive
404 for cases they cannot access. Message authors and requesters come from the
authenticated user, never request-body IDs.

**Authentication:** support and check-in use the auth feature's shared
`get_current_user` through `features/users/dependencies.py`. Log in with
`POST /api/v1/auth/login`, then send `Authorization: Bearer <access_token>`.
Missing, invalid, expired, and purpose-specific email/reset tokens return 401,
as do tokens for deleted or disabled users. No client-supplied user-ID header
is accepted. Integration tests exercise login and protected requests with real
JWTs; focused permission tests also use dependency overrides.

Remaining integrations: order/ticket context and private-event attendee access
once order/ticket ownership exists, and notifications once that feature exists.

## Check-in staff access (part 5)

All routes are under `/api/v1/checkin` and require the shared authenticated user:

| Method | Route | Purpose |
| --- | --- | --- |
| GET | `/events` | List the current user's owned/assigned events, excluding cancelled/suspended events |
| POST | `/staff?event_id=...` | Assign an existing active user to an event |
| GET | `/staff?event_id=...` | List an event's staff |
| DELETE | `/staff?event_id=...&assignment_id=...` | Revoke an assignment |

Only the event owner or a `platform_admin` can manage assignments. Lists accept
`limit` (1–100, default 50) and `offset` (default 0). Platform admins can see all
events excluding cancelled and suspended ones. An assignment request contains:

```json
{
  "user_id": "existing-user-uuid",
  "can_undo_check_in": false,
  "can_manage_support": false
}
```

Each assignment grants scanner access for that event. Undo and support access
are opt-in. Duplicate user/event assignments return 409, enforced with a database
unique constraint. To change permissions, revoke the assignment and create a new
one. Revocation removes event and support access on subsequent requests; stored
support conversations remain intact.

## Ticket scanner API

The scanner routes require a login token and the selected `event_id` query
parameter. Owners and platform admins have scanner/undo access; assigned staff
can scan and need `can_undo_check_in=true` to reverse entry.

| Method | Route | Purpose |
| --- | --- | --- |
| GET | `/api/v1/tickets/verify?event_id=...&qr_token=...` | Check an admission QR and its current status |
| POST | `/api/v1/tickets/check-in?event_id=...&ticket_id=...` | Record admission |
| POST | `/api/v1/tickets/undo-check-in?event_id=...&ticket_id=...` | Reverse an accidental admission |

The selected event is required even for owners/admins, and the ticket must belong
to it. Unknown tokens, Campaign QR tokens/links, and tickets from another event
return `valid=false`, `status=not_found`, and no ticket data from verification.
Missing authentication returns 401; an inaccessible event or wrong-event ticket
ID returns 404; insufficient undo permission returns 403. Cancelled/suspended
events return 400. A ticket's order must exist, match the event, and be paid.
Verification reports non-paid order status as invalid even when the ticket's
stored status is still `valid`.

Check-in (`valid` to `checked_in`) and undo (`checked_in` to `valid`) use conditional
database updates; overlapping requests can change the state only once. Undo also
matches the admission timestamp so a stale reversal cannot undo a later entry.
Failed transitions return 400. Each successful change writes an audit entry with
the event, ticket, acting user, and timestamp in the same transaction.

## Orders and attendee tickets

Orders, payments and attendee ticket routes require a login token. An order item
sends only `ticket_type_id` and `quantity`; the name and price come from the
stored ticket type. The event must be published, the ticket type must belong to
it, be visible and on sale, and the quantity must respect `max_per_order`.

Creating an order reserves stock with a conditional update and returns 409 when
not enough is left. A successful payment, or a free order, moves the stock from
reserved to sold. Cancelling a pending order releases it.

`GET /orders` and `GET /tickets` return only the caller's own records. Order,
payment, ticket detail and PDF are visible to the buyer, the event organizer and
platform admins; anyone else gets 404. Only the buyer can pay an order.

Still open: reservations do not expire, and cancelling or refunding a paid order
does not invalidate its tickets yet.
