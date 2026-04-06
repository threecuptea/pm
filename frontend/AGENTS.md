# Frontend AGENTS

## Purpose

The `frontend/` app is a Next.js Kanban UI demo used as the initial user-facing MVP surface. It currently runs as a client-heavy app with in-memory board state and no backend integration yet.

## Current stack

- Next.js 16 (App Router)
- React 19
- TypeScript
- Tailwind CSS 4
- dnd-kit for drag and drop
- Vitest + Testing Library for unit/component tests
- Playwright for end-to-end tests

## Key behavior today

- First visit to `/` shows a login screen.
- Login credentials are hardcoded to `user` / `password` (frontend-only gate).
- After successful login, renders a single Kanban board at `/`.
- Includes a logout action that returns to the login screen.
- Board has 5 fixed columns from seed data.
- Column titles are editable inline.
- Cards can be added and removed.
- Cards can be moved by drag and drop within and across columns.
- Board state is loaded from backend (`GET /api/board`) after login.
- Board updates are persisted to backend (`PUT /api/board`) and survive reload.
- AI sidebar is available next to the board after login.
- Sidebar sends chat prompts to backend (`POST /api/ai/chat`).
- AI message responses are shown inline in chat history.
- When AI returns `board_updated=true`, board UI refreshes immediately with returned board state.

## Code map

- `src/app/page.tsx`
  - App entry point for `/`, renders `KanbanBoard`.
- `src/components/KanbanBoard.tsx`
  - Top-level board state and drag/drop wiring.
  - Handles rename/add/delete/move operations.
  - Loads/saves board state via backend API.
- `src/components/AuthGate.tsx`
  - Frontend-only auth gate, login validation, session storage persistence, and logout.
- `src/components/KanbanColumn.tsx`
  - Column UI, droppable area, sortable context, and per-column add form.
- `src/components/KanbanCard.tsx`
  - Sortable card UI and card deletion action.
- `src/components/NewCardForm.tsx`
  - Expandable form for card creation.
- `src/components/KanbanCardPreview.tsx`
  - Drag overlay preview card.
- `src/lib/kanban.ts`
  - Board types, seed data, `moveCard` logic, and `createId` helper.
- `src/lib/api.ts`
  - Frontend API helpers for board fetch/save operations and AI chat.

## Test map

- `src/components/KanbanBoard.test.tsx`
  - Verifies render count, column rename, add/remove card behavior, AI chat rendering, and AI board update application.
- `src/components/AuthGate.test.tsx`
  - Verifies login visibility, invalid credentials error, and login/logout flow.
- `src/lib/kanban.test.ts`
  - Unit tests for board move logic.
- `src/lib/api.test.ts`
  - Unit tests for board API helper success/error behavior.
- `tests/kanban.spec.ts`
  - Browser flows for login, load, add card, drag card between columns, logout, and AI chat board update reflection.
- `tests/persistence.spec.ts`
  - Browser flow verifying board persistence across page reload.
- `test/setup.ts`
  - Testing setup for unit tests.

## Commands

- Install: `npm install`
- Dev server: `npm run dev`
- Build: `npm run build`
- Unit tests: `npm run test:unit`
- E2E tests: `npm run test:e2e`
- All tests: `npm run test:all`
- Backend deps sync (from repo root): `cd backend && uv sync --group dev`
- Backend tests (from repo root): `cd backend && uv run pytest tests -q`

## Conventions for future edits

- Keep board domain types centralized in `src/lib/kanban.ts` unless a backend model layer is introduced.
- Prefer small, focused React components with explicit props and callback handlers.
- Preserve existing `data-testid` patterns used by tests (`column-*`, `card-*`).
- Update unit and e2e tests together when changing interactive board behavior.
- Keep UI behavior simple and MVP-focused; avoid adding non-required settings or flows.
