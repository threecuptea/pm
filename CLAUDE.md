# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Project Management MVP web application with a React/Next.js frontend and Python FastAPI backend. Key features include user sign-in, a Kanban board with drag-and-drop cards, and an AI chat sidebar that can create/edit/move cards.

**Tech Stack:**
- Frontend: Next.js 16 + React 19 + Tailwind CSS
- Backend: FastAPI (Python 3.12+) with SQLite
- AI: OpenRouter API (GPT-OSS-120B)
- Deployment: Docker and docker-compose

## Common Commands

### Running Locally

**Start the application:**
```bash
./scripts/start-mac.sh       # Mac
./scripts/start-windows.ps1  # Windows
./scripts/start-linux.sh     # Linux
```
This builds and starts the Docker container. App runs at http://localhost:8000

**Stop the application:**
```bash
./scripts/stop-mac.sh        # Mac
./scripts/stop-windows.ps1   # Windows
./scripts/stop-linux.sh      # Linux
```

**Manual Docker commands:**
```bash
docker compose up --build -d   # Start in background
docker compose down             # Stop
docker compose logs -f          # View logs
```

### Frontend Development (without Docker)

Navigate to `frontend/` directory:

```bash
npm install           # Install dependencies
npm run dev           # Start dev server (http://localhost:3000)
npm run build         # Build for production
npm run start         # Run production build locally
npm run lint          # Run ESLint

# Testing
npm run test:unit           # Run unit tests (Vitest)
npm run test:unit:watch     # Run unit tests in watch mode
npm run test:e2e            # Run E2E tests (Playwright)
npm run test:all            # Run all tests
```

**Running a single test file:**
```bash
npx vitest run src/path/to/test.test.ts                    # Unit test
npx playwright test src/e2e/path/to/test.spec.ts           # E2E test
```

### Backend Development (without Docker)

Navigate to `backend/` directory:

```bash
# Setup (if needed)
python -m venv .venv
source .venv/bin/activate  # or .\.venv\Scripts\activate on Windows

# With uv (recommended)
uv sync                     # Install dependencies including dev
uvicorn app.main:app --reload --port 8000  # Run dev server

# Testing
pytest                      # Run all tests
pytest tests/test_main.py   # Run single test file
pytest tests/test_main.py::test_function_name  # Run single test
pytest -v                   # Verbose output
pytest -k "keyword"         # Run tests matching keyword
```

**Backend API test:**
```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/api/sample
```

## Architecture

### Frontend (`frontend/`)

**Key directories:**
- `src/app/` - Next.js app directory with pages and layouts
- `src/components/` - React components (Board, Card, ChatSidebar, etc.)
- `src/lib/` - Utility functions and API clients
- `src/test/` - Test setup and utilities

**Key patterns:**
- Uses `@dnd-kit` for drag-and-drop functionality
- Tailwind CSS for styling with custom color variables (yellow accent `#ecad0a`, blue `#209dd7`, purple `#753991`)
- Fetch API for HTTP requests to backend
- Vitest for unit tests, Playwright for E2E tests

### Backend (`backend/`)

**Key directories:**
- `app/main.py` - FastAPI application and route definitions
- `app/repository.py` - KanbanRepository: database operations, board state management
- `app/ai.py` - OpenRouterClient for AI chat integration
- `app/*_schema.py` - Pydantic schemas for request/response validation
- `db/schema.sql` - SQLite schema
- `data/` - SQLite database file (created on first run)
- `tests/` - Test files

**API endpoints:**
- `GET /api/health` - Health check, returns `{"status": "ok"}`
- `GET /api/sample` - Test endpoint, returns `{"message": "Backend API is reachable."}`
- `GET /api/board?username=user` - Get board state for user
- `PUT /api/board?username=user` - Save/update board state (validates board structure)
- `POST /api/ai/chat?username=user` - AI chat: sends current board + chat history, receives structured response with optional board updates
- `GET /api/ai/test?prompt=...` - Test AI connectivity, returns `{"model": "...", "prompt": "...", "response": "..."}`

**AI Chat Flow:**
1. Frontend sends question + chat history to `/api/ai/chat`
2. Backend includes current board context in system message
3. OpenRouter returns structured JSON with `assistant_response` and optional `board_update`
4. Backend validates and persists any board updates
5. Returns updated board state to frontend

**AI Response Schema:**
```json
{
  "model": "gpt-oss-120b",
  "assistant_response": "Human-readable reply",
  "board_updated": true | false,
  "board": <full board object>
}
```

**Key patterns:**
- Repository pattern for data access (KanbanRepository)
- OpenRouter API client for AI (GPT-OSS-120B model via openai/gpt-oss-120b)
- Pydantic models for request/response validation (BoardPayload, AiChatRequest, AiChatResponse)
- SQLite database with auto-initialization on startup
- JSON schema validation for structured AI outputs

### Database

**Schema:** `backend/db/schema.sql` - SQLite with auto-creation on startup
- **users**: Username, created_at, updated_at
- **boards**: Stores complete board state as JSON (one per user, keyed by `board_key="main"`)
- **Default bootstrap**: Automatically creates user "user" and initial Kanban board on first run

**Board JSON structure:**
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

**Database location:** `backend/data/app.db` (or `PM_DB_PATH` env var)
- Reset by deleting the file; it will be recreated on next run
- Validation: each `cardIds` entry must exist in cards object

## Important Implementation Details

**Board State Management:**
- Board is a complete snapshot (not change history) stored as JSON in SQLite
- Frontend and backend both validate board structure
- Cards must exist in the cards object before being referenced in column `cardIds`
- All board changes go through `PUT /api/board` or AI chat updates

**Authentication (MVP):**
- Hardcoded username "user" / password "password"
- Query parameter `username` determines which user's board to load
- Future: upgrade to real auth but database schema already supports multiple users

**Frontend Build:**
- Built with `next build` which creates static output in `out/`
- Docker copies the static files to be served by FastAPI at `/`
- For local frontend-only development, use `npm run dev` (no Docker needed)

**Error Handling:**
- API returns `422` for invalid board payloads
- `502` for OpenRouter failures
- `503` for missing `OPENROUTER_API_KEY`
- All validation happens at the service layer before persistence

## Important Notes

1. **Simplicity is paramount**: The project intentionally avoids over-engineering. No unnecessary defensive programming or speculative features.
2. **Color scheme**: Always use the defined colors (yellow `#ecad0a`, blue `#209dd7`, purple `#753991`, navy `#032147`, gray `#888888`)
3. **Database**: SQLite is local and auto-created. Reset by deleting `backend/data/app.db`
4. **Environment setup**: 
   - Local development requires `.env` file with `OPENROUTER_API_KEY` (required for AI features)
   - The app will return 503 if `OPENROUTER_API_KEY` is missing
   - Default username is "user" with password "password" (MVP authentication)
5. **Frontend-only development**: For frontend work, run `npm run dev` in the `frontend/` directory and mock API responses as needed
6. **Docker build**: The Dockerfile builds the frontend first (with `next build`), then runs the backend with the static files served at `/`
7. **Testing strategy**: Unit tests for logic, E2E tests for user workflows. Backend tests use pytest with test fixtures.

## Documentation References

- Project requirements and technical decisions: `AGENTS.md`
- Planning and execution docs: `docs/PLAN.md`
