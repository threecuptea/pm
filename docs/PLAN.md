# Project Plan

Execution rule for all parts:
- Keep part-level order and explicit user approval checkpoints.
- Allow only low-risk prep work from the next part when it prevents duplicate work.
- Keep implementation simple and focused on MVP only.

## Part 1: Plan and baseline documentation

Status:
- Completed (approved)

Scope:
- Expand this file with actionable checklists, tests, and success criteria.
- Add `frontend/AGENTS.md` describing the current frontend codebase and how to work in it.

Checklist:
- [x] Confirm execution rule, approval flow, and planning assumptions.
- [x] Expand all parts (2-10) with implementation checklist, tests, and success criteria.
- [x] Add `frontend/AGENTS.md` documenting current architecture, scripts, tests, and conventions.
- [x] Request and receive user approval on this plan before implementing Part 2.

Tests:
- [x] Manual review that each part includes objective, checklist, tests, and success criteria.

Success criteria:
- `docs/PLAN.md` is detailed enough to execute without ambiguity.
- `frontend/AGENTS.md` accurately reflects current frontend behavior and test setup.
- User explicitly approves plan progression.

## Part 2: Scaffolding (Docker + FastAPI + scripts)

Status:
- Completed (approved)

Objective:
- Create the initial deployable app shell with Docker, backend service, and cross-platform start/stop scripts.
- Do not keep a temporary hello-world page; move directly to serving app/static assets pathing needed for next part.

Checklist:
- [x] Create backend FastAPI app structure in `backend/`.
- [x] Add health endpoint and at least one API route for smoke checks.
- [x] Add Dockerfile and required config to run full stack in one container.
- [x] Add start/stop scripts for macOS, Linux, and Windows in `scripts/`.
- [x] Add low-risk prep for Part 3: static file mounting path and routing shape.
- [x] Document run commands minimally in top-level docs as needed.

Tests:
- Automated:
	- [x] Backend unit test for health route.
	- [x] Backend test for sample API route.
- Manual:
	- [x] Build container successfully.
	- [x] Start app via scripts on host.
	- [x] Confirm API route responds from running container.

Verification notes:
- Docker image and compose wiring validated.
- `/api/health` and `/api/sample` verified via curl.

Success criteria:
- App boots through scripts and Docker with no manual patching.
- Backend routes respond successfully.
- Scaffold supports immediate transition to static frontend serving.

## Part 3: Serve the existing frontend from backend

Status:
- Completed (approved)

Objective:
- Build frontend statically and serve it from FastAPI at `/`, showing current Kanban demo.

Checklist:
- [x] Add frontend build step to container/runtime flow.
- [x] Configure backend static file serving for Next.js build output strategy chosen.
- [x] Wire route handling so `/` renders the Kanban app.
- [x] Ensure API namespace does not conflict with frontend routes.
- [x] Keep changes minimal and compatible with current tests.

Tests:
- Automated:
	- [x] Frontend unit tests pass.
	- [x] Frontend e2e smoke test against served app path.
	- [x] Backend route tests still pass.
- Manual:
	- [x] Open `/` and verify Kanban board renders with columns and cards.

Verification notes:
- Multi-stage Docker build exports frontend and serves it at `/`.
- API routes remained healthy while static frontend was served.

Success criteria:
- Containerized app serves frontend at `/`.
- Existing frontend interactions continue working.
- Test suite for touched areas passes.

## Part 4: Fake sign-in gate (frontend-only)

Status:
- Completed (approved)

Objective:
- Add an MVP login experience at `/` requiring credentials `user` / `password` before showing Kanban.
- Use frontend-only gating until backend auth routes are added later.

Checklist:
- [x] Add login screen/state in frontend.
- [x] Validate hardcoded credentials exactly (`user`, `password`).
- [x] Persist authenticated state for current browser session.
- [x] Add logout control and reset auth state.
- [x] Keep unauthenticated users blocked from board UI.

Tests:
- Automated:
	- [x] Unit tests for login success/failure paths.
	- [x] Unit test for logout behavior.
	- [x] E2E flow: blocked -> login success -> board visible -> logout -> blocked.
- Manual:
	- [x] Invalid credentials show clear error.
	- [x] Reload behavior matches chosen session persistence rule.

Success criteria:
- Only valid dummy credentials unlock board.
- Logout re-locks board.
- Auth gate is clearly frontend-only and isolated for later backend replacement.

## Part 5: Database modeling and sign-off

Status:
- Completed (approved)

Objective:
- Define SQLite schema and JSON persistence strategy for one board per user (multi-user capable schema).

Checklist:
- [x] Propose schema for users, boards, and board JSON payload.
- [x] Define constraints and indexes needed for MVP.
- [x] Define JSON structure stored for board state.
- [x] Document migration/bootstrapping approach when DB file does not exist.
- [x] Add documentation in `docs/` and request explicit user sign-off.

Tests:
- Automated:
	- [x] Schema initialization test creates tables on empty DB.
	- [x] CRUD-oriented unit tests for board read/write at repository layer.
- Manual:
	- [x] Inspect created SQLite DB and confirm expected tables and rows.

Verification notes:
- Schema documented in `docs/DATABASE.md` and implemented in `backend/db/schema.sql`.

Success criteria:
- Schema and JSON approach are documented and approved.
- DB creation on first run is proven.
- Model cleanly supports one board per user in MVP while allowing future extension.

## Part 6: Backend API for Kanban persistence

Status:
- Completed (approved)

Objective:
- Implement backend routes to read/update user Kanban data via SQLite.

Checklist:
- [x] Add repository/service layer for DB operations.
- [x] Add API endpoints for fetching and saving board state.
- [x] Validate payload shape and return helpful error responses.
- [x] Ensure DB initializes automatically if missing.
- [x] Keep route surface minimal for MVP.

Tests:
- Automated:
	- [x] Endpoint tests for success and validation failures.
	- [x] Unit tests for repository methods.
	- [x] Test for first-run DB creation.
- Manual:
	- [x] Call API routes and verify persisted state survives restart.

Verification notes:
- Added `/api/board` GET/PUT with payload validation and persistence.
- Backend test suite passed (`6 passed`).

Success criteria:
- Backend provides reliable board read/write APIs.
- Invalid input is handled safely.
- Persistence works across process restarts.

## Part 7: Connect frontend to backend APIs

Status:
- Completed (verified)

Objective:
- Replace in-memory board usage with backend-backed persistence.

Checklist:
- [x] Add frontend API client helpers.
- [x] Load board state from backend on app load.
- [x] Persist board changes (rename, add, delete, drag/drop) via API.
- [x] Add loading/error states with simple UX.
- [x] Keep local optimistic behavior only if needed for responsiveness and simplicity.

Tests:
- Automated:
	- [x] Unit tests for API client and state update handling.
	- [x] Integration/e2e tests proving persistence after reload.
- Manual:
	- [x] Edit board, refresh, and confirm changes remain.

Verification notes:
- Standard e2e suite passed for login/board interactions.
- Backend-integrated persistence test passed with dockerized app (reload retains updates).

Success criteria:
- Board state is backend-sourced and persistent.
- Core board actions remain stable and test-covered.

## Part 8: AI connectivity via OpenRouter

Status:
- Completed (verified)

Objective:
- Add backend capability to call OpenRouter using `openai/gpt-oss-120b`.

Checklist:
- [x] Add OpenRouter client configuration using `OPENROUTER_API_KEY`.
- [x] Implement simple AI test route/service call.
- [x] Add secure config handling and clear missing-key errors.
- [x] Add a connectivity verification test path using prompt `2+2`.

Tests:
- Automated:
	- [x] Unit test with mocked provider response.
	- [x] Integration test path with mocked HTTP client.
- Manual:
	- [x] Live connectivity check (when key available) returns a plausible answer to `2+2`.

Verification notes:
- Added `/api/ai/test` endpoint backed by OpenRouter client.
- Missing API key now returns clear `503` message.
- Backend suite passed (`9 passed`) including new AI tests.
- Dockerized live connectivity check returned `4` for prompt `2+2`.

Success criteria:
- Backend can successfully call OpenRouter.
- Missing/invalid key cases are understandable and non-crashing.

## Part 9: Structured output for AI + Kanban updates

Status:
- Completed (verified)

Objective:
- Extend AI call to send board JSON + user message + history and receive structured response with optional board update.
- Backfill docs immediately after implementation.

Checklist:
- [x] Implement structured response schema in backend code.
- [x] Include board JSON and conversation context in AI request.
- [x] Parse and validate structured AI response.
- [x] Apply optional board updates safely and persist when present.
- [x] Backfill documentation in `docs/` right after code lands.

Tests:
- Automated:
	- [x] Unit tests for schema validation and parse failures.
	- [x] Tests for both response types: message-only and message+board-update.
	- [x] Persistence tests for AI-driven updates.
- Manual:
	- [ ] Ask a question that should not modify board and verify no mutation.
	- [ ] Ask a command-like request and verify expected board mutation.

Verification notes:
- Added `POST /api/ai/chat` with structured JSON-schema output handling.
- Backend now always sends current board JSON, conversation history, and user question to AI.
- Optional AI board updates are validated and persisted through repository layer.
- Added and passed structured AI tests for message-only, update-and-persist, and invalid payload handling.
- Backend suite passed (`13 passed`).

Success criteria:
- AI responses are structured and validated.
- Optional board mutation path is reliable and persisted.
- Documentation matches implemented schema and behavior.

## Part 10: Frontend AI sidebar and live board refresh

Objective:
- Add AI chat sidebar that sends/receives messages and applies AI-driven board updates to UI automatically.

Checklist:
- [ ] Build sidebar chat UI integrated into existing board page.
- [ ] Show conversation history and loading/error states.
- [ ] Connect sidebar to backend AI endpoint.
- [ ] Apply returned board updates to frontend state automatically.
- [ ] Ensure layout is responsive and works on desktop/mobile.

Tests:
- Automated:
	- [ ] Component tests for chat interactions and rendering states.
	- [ ] Integration/e2e tests for chat submit, response render, and board update reflection.
- Manual:
	- [ ] Validate no-update AI responses keep board unchanged.
	- [ ] Validate update responses refresh board without manual reload.

Success criteria:
- Sidebar chat is usable and stable.
- AI-requested board updates appear immediately in UI and persist through backend.
- End-to-end MVP behavior (sign-in, Kanban operations, AI assist) is complete in containerized local run.