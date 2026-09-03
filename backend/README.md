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
- A feature may import from `core` and from another feature's `service`, `models`
  or `schemas`. It must not import another feature's `routes`.
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

app.include_router(events.routes.router)
```

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
uv run mypy app core tests
```
