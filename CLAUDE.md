# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Project Management MVP: React/Next.js frontend + Python FastAPI backend. Features: user sign-in, Kanban board with drag-and-drop cards, AI chat sidebar that can create/edit/move cards.

**Tech Stack:**
- Frontend: Next.js 16 + React 19 + Tailwind CSS 4
- Backend: FastAPI (Python 3.12+) with SQLite
- AI: OpenRouter API (`openai/gpt-oss-120b`)
- Deployment: Single Docker container (multi-stage build)
- Package managers: npm (frontend), uv (backend)

## Common Commands

### Docker (full stack)
```bash
docker compose up --build -d   # Start (app at http://localhost:8000)
docker compose down             # Stop
docker compose logs -f          # View logs
```
Platform scripts in `scripts/`: `start-mac.sh`, `stop-mac.sh`, etc.

### Frontend (`cd frontend/`)
```bash
npm install && npm run dev      # Dev server at http://localhost:3000
npm run build                   # Static export to out/
npm run lint                    # ESLint

# Tests
npm run test:unit               # Vitest
npm run test:e2e                # Playwright (starts dev server automatically)
npx vitest run src/path/to/test.test.ts              # Single unit test
npx playwright test tests/kanban.spec.ts             # Single E2E test

# E2E against Docker container
PLAYWRIGHT_BASE_URL=http://localhost:8000 PLAYWRIGHT_NO_WEBSERVER=1 npx playwright test
```

### Backend (`cd backend/`)
```bash
uv sync                                              # Install deps
uvicorn app.main:app --reload --port 8000            # Dev server

# Tests
pytest                                               # All tests
pytest tests/test_main.py                            # Single file
pytest tests/test_main.py::test_function_name        # Single test
pytest -k "keyword"                                  # By keyword
```

## Architecture

### How the pieces connect

**Docker build:** Dockerfile stage 1 builds the Next.js frontend as a static export (`output: "export"` in next.config.ts). Stage 2 runs the FastAPI backend, which serves those static files at `/` via StaticFiles mount. Everything runs in a single container on port 8000.

**Frontend-backend communication:** All API calls go to `/api/*` endpoints. The frontend uses the Fetch API (see `src/lib/api.ts`). CORS middleware allows `localhost:3000` and `127.0.0.1:3000` for local frontend-only development.

**Board save flow:** KanbanBoard debounces saves with a 180ms timer. On unmount, it flushes any pending save via `navigator.sendBeacon` to avoid data loss (see `KanbanBoard.tsx`).

**AI chat flow:** Frontend sends question + chat history to `POST /api/ai/chat`. Backend injects current board state as system context, calls OpenRouter with JSON schema constraints, validates the structured response, persists any board updates, and returns the updated board to the frontend. The `ai_test` and `ai_chat` routes are async, using `httpx.AsyncClient` via `async with` for non-blocking HTTP calls to OpenRouter.

### Board state model

Board is a complete snapshot stored as JSON in SQLite (not a change history):
```json
{
  "columns": [
    { "id": "col-backlog", "title": "Backlog", "cardIds": ["card-1"] }
  ],
  "cards": {
    "card-1": { "id": "card-1", "title": "Title", "details": "Details" }
  }
}
```
**Validation constraint:** Every `cardIds` entry must exist in the `cards` map, and there must be no orphan cards. Both frontend and backend enforce this.

**Duplicate default board data:** Initial board content is defined in both `frontend/src/lib/kanban.ts` (initialData) and `backend/app/default_board.py`. These must be kept in sync.

### Backend structure

- `app/main.py` - FastAPI app, route definitions, static file serving
- `app/repository.py` - KanbanRepository: SQLite operations using `with conn` context manager
- `app/ai.py` - OpenRouterClient with sync (`ask`, `ask_structured`) and async (`ask_async`, `ask_structured_async`) methods. Async methods use `httpx.AsyncClient` passed in from the caller.
- `app/board_schema.py`, `app/ai_chat_schema.py` - Pydantic request/response models
- `db/schema.sql` - SQLite schema (users + boards tables, auto-created on startup)
- `data/app.db` - SQLite database (or `PM_DB_PATH` env var). Delete to reset.

### Frontend structure

- `src/lib/api.ts` - API client (fetchBoard, saveBoard, chatWithAi)
- `src/lib/kanban.ts` - Board types, moveCard logic, ID generation
- `src/components/KanbanBoard.tsx` - Main board component with dnd-kit, debounced save
- `src/components/AiSidebar.tsx` - AI chat interface
- `src/components/AuthGate.tsx` - Login gate (hardcoded "user"/"password", session storage)

### Testing details

- **Backend tests** use `tmp_path` fixture for DB isolation (see `conftest.py`). `pythonpath = [".."]` in pyproject.toml enables absolute imports like `backend.app.main` in tests. AI route tests mock `httpx.AsyncClient` with fake async context managers (`__aenter__`/`__aexit__`) and async `post()` methods.
- **Frontend unit tests** use jsdom via Vitest. Setup in `src/test/setup.ts` mocks `navigator.sendBeacon`.
- **Playwright E2E** runs against dev server by default. The `persistence.spec.ts` test only runs against Docker (`PLAYWRIGHT_NO_WEBSERVER=1`).

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/board?username=user` - Get board state
- `PUT /api/board?username=user` - Save board (422 on invalid payload)
- `POST /api/ai/chat?username=user` - AI chat (502 on OpenRouter failure, 503 if no API key)
- `GET /api/ai/test?prompt=...` - Test AI connectivity

## Important Notes

1. **Simplicity is paramount**: No over-engineering, no unnecessary defensive programming, no speculative features. Always identify root cause before fixing issues.
2. **No emojis** in code or documentation.
3. **Color scheme**: yellow `#ecad0a`, blue `#209dd7`, purple `#753991`, navy `#032147`, gray `#888888`. Fonts: Space Grotesk (display), Manrope (body).
4. **Environment**: `.env` file at project root with `OPENROUTER_API_KEY` (required for AI features).
5. **Authentication (MVP)**: Hardcoded username "user" / password "password". DB schema supports multiple users for future.
6. **Static export**: Frontend uses `output: "export"` — no SSR or server components. All pages are statically generated.

## Documentation References

- Project requirements and coding standards: `AGENTS.md`
- Planning and execution docs: `docs/PLAN.md`
