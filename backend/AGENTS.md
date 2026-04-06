# Backend AGENTS

## Purpose

The `backend/` directory contains the FastAPI service that powers API routes and, in later parts, will serve the frontend build and persist Kanban state.

## Current implementation (Part 8)

- FastAPI app entry point: `backend/app/main.py`
- Routes:
	- `GET /api/health` -> `{ "status": "ok" }`
	- `GET /api/sample` -> `{ "message": "Backend API is reachable." }`
	- `GET /api/board?username=user` -> current board JSON for user
	- `PUT /api/board?username=user` -> validates and persists board JSON
	- `GET /api/ai/test?prompt=2+2` -> OpenRouter completion response
- Static frontend serving:
	- Exported frontend assets are served at `/`.
	- Docker build generates frontend static output and copies it to `/app/frontend_out`.
- Database modeling artifact (Part 5):
	- SQL schema draft in `backend/db/schema.sql`.

- Persistence behavior:
	- SQLite database auto-creates on first run at `backend/data/app.db`.
	- Default `user` and `main` board are bootstrapped automatically.
	- Repository layer implemented in `backend/app/repository.py`.
- AI behavior:
	- OpenRouter client implemented in `backend/app/ai.py`.
	- Uses model `openai/gpt-oss-120b`.
	- Returns clear errors for missing key and upstream failures.

## Dependency management

- Uses `uv` and `backend/pyproject.toml`.
- Sync dependencies: `uv sync --project backend --group dev`
- Run tests: `uv run --project backend pytest backend/tests -q`

## Testing

- Tests live in `backend/tests/`.
- Current coverage verifies health and sample API routes.

## Conventions

- Keep routes under `/api/*` to avoid frontend route conflicts.
- Keep backend changes minimal and MVP-focused.
- Add tests for each new route or behavior change.