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

## Commands

```bash
npm run dev
npm run build
npm run lint
npm run typecheck
npm run format
```
