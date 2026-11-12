# BiletFlow

Self-service event ticketing platform for Kazakhstan. Organizers publish events and
issue QR-code tickets; attendees register, pay in KZT and check in at the door.

## Stack

| Part     | Technology                                                    |
| -------- | ------------------------------------------------------------- |
| Backend  | FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, Pydantic          |
| Frontend | React 19, TypeScript, Vite, Tailwind CSS, shadcn/ui           |
| Mobile   | Ticket verification app for event admins                      |
| Tooling  | uv, Ruff, mypy, pytest, oxlint, Prettier, Docker Compose      |

Both sides are feature-sliced: the backend splits into `core/` plus `features/<name>/`,
the web client follows Feature-Sliced Design. Each sub-project documents its own
architecture and coding rules in its README.

## Requirements

- Python 3.13+ and [uv](https://docs.astral.sh/uv/)
- Node.js 24+
- Docker (for PostgreSQL, or run your own instance)

## Getting started

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

docker compose up -d postgres mailpit
make install
make migrate
```

Run the two services in separate shells:

```bash
make dev-backend
```

```bash
make dev-frontend
```

The API is served at `http://localhost:8000` with interactive docs at `/docs`.
The web client runs at `http://localhost:5173` and proxies `/api` to the backend.
Sent emails show up in Mailpit at `http://localhost:8025`.

## Common tasks

```bash
make help          # list every target
make lint          # ruff + mypy + oxlint + tsc
make format        # ruff format + prettier
make test          # backend test suite
make migration m="add events"
make seed          # demo users and event, dev only
make up            # full stack in Docker
```

For the full stack in Docker, migrate and seed inside the backend container:

```bash
make up
docker compose exec backend alembic upgrade head
docker compose exec backend python -m scripts.seed
```

After `uv.lock` changes, rebuild with `docker compose up -d --build -V` so the
backend container gets a fresh virtualenv.

Demo accounts created by `make seed`, all with password `password123`:
`attendee@biletflow.dev`, `organizer@biletflow.dev`, `eventadmin@biletflow.dev`
and `admin@biletflow.dev`.

## Repository layout

```
backend/    FastAPI service (REST API, database, migrations)
frontend/   React web client for attendees, organizers and platform admins
mobile/     Ticket verification app for event admins
```

See [backend/README.md](backend/README.md) and [frontend/README.md](frontend/README.md)
for the layout and conventions inside each.

## Contributing

- `main` is protected; work happens on branches.
- Branch names: `feat/<scope>`, `fix/<scope>`, `chore/<scope>`, `docs/<scope>`.
- Commits follow Conventional Commits: `feat(events): add draft publication`.
- One logical change per pull request; rebase rather than merge to keep history linear.
- `make lint` and `make test` pass locally before you open the pull request.

## Naming

Files and directories are `kebab-case` everywhere. Language-specific rules —
Python modules, database tables, React components — are in the backend and
frontend READMEs.

## Comments

Default to none. Clear naming, small functions and type hints carry the meaning;
a comment restating what the line already says is noise that goes stale.

Write one only when the code cannot explain itself:

- A non-obvious *why*: a workaround, a constraint from the payment provider, a
  deliberate ordering, a rule that comes from the spec rather than the code.
- A `TODO:` that names the condition, not a vague wish —
  `TODO: replace with the real provider webhook once sandbox keys arrive`.
- A short docstring on a module or class whose purpose is not obvious from its name.

Never:

- Comments that narrate the next line (`# create the user`, `// set loading true`).
- Section banners and decorative separators.
- Commented-out code. Delete it; git remembers.
- Notes addressed to nobody (`# this is important`, `# fixed the bug`).

Review rejects a diff whose comments only restate its code.
