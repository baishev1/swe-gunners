# BiletFlow Web

React client for attendees, organizers and platform administrators.

## Setup

```bash
npm install
cp .env.example .env
npm run dev
```

## Feature-Sliced Design

```
src/
  app/       providers, router, global styles
  pages/     route-level compositions
  widgets/   self-contained blocks combining features and entities
  features/  user actions with their own state and API calls
  entities/  domain models and their presentation
  shared/    framework-agnostic utilities, UI kit, API client, config
```

A layer may import only from the layers beneath it. Every slice exports its public
API from `index.ts`; importing a slice's internals from outside is not allowed.

## UI components

shadcn/ui primitives are generated into `src/shared/ui` and are part of the shared
UI kit:

```bash
npx shadcn@latest add dialog
```

Do not edit a generated primitive unless the change is intentional and documented.

## Conventions

- TypeScript strict mode, no `any`.
- Imports use the `@/` alias; relative imports stay within a slice.
- Server state lives in TanStack Query. Add a client-state or form library when
  a slice actually needs one.
- Components are function declarations with named exports, named `PascalCase`.
  Hooks are `useCamelCase`.

## Translations

The interface is available in Kazakh, Russian and English. Setup lives in
`src/shared/i18n`, strings in `src/shared/i18n/locales/{kk,ru,en}.json`. Russian is
the default, English the fallback. The choice is stored in `localStorage`.

Adding a string:

1. Add the key to all three JSON files, grouped by page or feature
   (`login.title`, `eventForm.venue`). Reuse `common.*` for shared words.
2. In the component: `const { t } = useTranslation()`, then `t('login.title')`.
   Values go in as `t('register.checkEmailDescription', { email })`.

Do not translate backend `detail` messages. Pass dates and prices through
`formatDateTime` and `formatPrice` from `@/shared/lib/format`, which use the active
language.

Adding a language:

1. Create `locales/<code>.json` with the same keys as `en.json`.
2. Register it in `resources` and in `LANGUAGES` in `src/shared/i18n/index.ts`.

The switcher in the `src/widgets/app-header` header picks the new code up from `LANGUAGES`.

## End-to-end tests

Playwright specs live in `e2e/` and run in Chromium against the real API. The UI
language is forced to English before each test. Playwright starts the Vite dev
server itself (or reuses one on port 5173) but not the backend. Test runs leave
extra users and events in the database.

From the repo root:

```bash
docker compose up -d postgres
make migrate
make seed
make dev-backend
cd frontend && npx playwright install chromium   # first run only
npm run e2e
```

The registration test needs `uv` on the PATH: it asks the backend code for the
email verification token, since no mail is sent.

## Commands

```bash
npm run dev
npm run build
npm run lint
npm run typecheck
npm run format
npm run e2e
```
