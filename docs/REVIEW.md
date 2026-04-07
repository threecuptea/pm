# Code Review

Comprehensive review of the full repository. Each finding includes severity, location, and a recommended action.

Severity scale: **Critical** (must fix before any deployment), **High** (significant risk or correctness issue), **Medium** (quality/maintainability), **Low** (minor improvement).

---

## High

### 1. Board validation does not check for orphan cards

**Location:** `backend/app/board_schema.py:26-38`

The validator ensures every `cardIds` entry exists in the `cards` map, but does not check the reverse: cards that exist in the map but are not referenced by any column. Orphan cards silently accumulate and are invisible to the user.

**Action:** Add a check that every key in `cards` appears in at least one column's `cardIds` list, or decide explicitly that orphans are acceptable and document why.

### 2. SQLite connections are never explicitly closed

**Location:** `backend/app/repository.py:77-81`

`_connect()` returns a raw `sqlite3.Connection`. Callers use `with self._connect() as conn:`, which commits/rolls back the transaction but does **not** close the connection (SQLite's context manager only manages transactions). Connections accumulate until garbage-collected.

**Action:** Close connections explicitly after use, e.g. wrap in a try/finally or use `contextlib.closing`.

### 3. `_ensure_user` silently updates `updated_at` on every read

**Location:** `backend/app/repository.py:62-75`

The upsert in `_ensure_user` runs `DO UPDATE SET updated_at = datetime('now')` on conflict. This means every `get_board` call updates the user's `updated_at` timestamp, making it meaningless for tracking actual user modifications.

**Action:** Use `INSERT OR IGNORE` instead, or only update `updated_at` in write paths (`save_board`).

### 4. Debounced save can lose data on rapid navigation

**Location:** `frontend/src/components/KanbanBoard.tsx:81-105`

The 180ms debounce timer is cleared on unmount, but the cleanup flush (`saveBoard(pendingBoardRef.current)`) fires-and-forgets with `.catch(() => {})`. If the component unmounts during a save (e.g. logout), the save may silently fail and the user loses their last edit.

**Action:** Consider awaiting the flush or displaying a warning if there are unsaved changes at logout time.

---

## Medium

### 5. Playwright E2E tests run against frontend dev server, not the Docker build

**Location:** `frontend/playwright.config.ts:16-23`

Default Playwright config starts `npm run dev` on port 3000 and tests against it. The persistence spec is skipped unless `PLAYWRIGHT_NO_WEBSERVER=1`. This means the standard E2E suite never tests the actual production build (static export served by FastAPI). Regressions in the Docker build path (e.g. static routing, API proxying) would not be caught.

**Action:** Add a CI step or documented command that runs E2E against the Docker container (`PLAYWRIGHT_BASE_URL=http://localhost:8000 PLAYWRIGHT_NO_WEBSERVER=1`).

### 6. Duplicate default board data

**Location:** `frontend/src/lib/kanban.ts:18-72` and `backend/app/default_board.py:4-60`

The default board (columns, cards, titles, details) is duplicated verbatim between frontend and backend. If either changes independently, the initial board experience diverges.

**Action:** Remove the frontend `initialData` as the default and rely solely on the backend response. Use a loading skeleton or empty state while the fetch completes, or fetch the board before rendering.

### 7. `sys.path` manipulation in every test file

**Location:** `backend/tests/test_main.py:7`, `test_board_api.py:7`, `test_ai.py:8`, `test_repository.py:7`

Every backend test file manually inserts the parent directory into `sys.path`. This is fragile and will break if the directory structure changes.

**Action:** Add a `conftest.py` that handles the path setup once, or configure pytest's `pythonpath` in `pyproject.toml` (e.g. `[tool.pytest.ini_options] pythonpath = [".."]`).

### 8. No CORS configuration

**Location:** `backend/app/main.py`

The FastAPI app has no CORS middleware. In the Docker build this is fine (same origin), but local frontend development (`npm run dev` on port 3000) calling the backend on port 8000 will fail due to cross-origin restrictions.

**Action:** Add `CORSMiddleware` with appropriate origins for local dev, or document the limitation and recommend using the Docker setup.

### 9. `row_factory` set but never used

**Location:** `backend/app/repository.py:79`

`conn.row_factory = sqlite3.Row` is set on every connection, but all queries access results by index (`row[0]`), not by column name. The setting is unused overhead and misleading.

**Action:** Either remove the `row_factory` assignment or switch to named column access for clarity.

### 10. KanbanBoard component is large and has mixed concerns

**Location:** `frontend/src/components/KanbanBoard.tsx` (390 lines)

This single component manages board state, drag-and-drop, debounced saving, AI chat state, AI submission, error states, and renders both the board and the AI sidebar. It holds 9 `useState` hooks and 3 refs.

**Action:** Extract the AI sidebar into its own component with its own state management. Pass a callback for board updates. This improves readability and testability.

---

## Low

### 11. Test fixture duplication across backend test files

**Location:** `backend/tests/test_main.py:12-15`, `test_board_api.py:12-15`

The `client` fixture (creating an app with `tmp_path`) is copy-pasted across test files.

**Action:** Move the shared `client` fixture to a `conftest.py`.

### 12. Frontend username is hardcoded in API client

**Location:** `frontend/src/lib/api.ts:3-4`

Both endpoint URLs embed `?username=user`. When real auth is added, these will need to change.

**Action:** Accept username as a parameter or read it from auth context. Low priority since this is documented as MVP-only.

### 13. `Content-Type` header on GET request is unnecessary

**Location:** `frontend/src/lib/api.ts:33`

`fetchBoard` sets `Content-Type: application/json` on a GET request with no body. Harmless but unnecessary.

**Action:** Remove the header from the GET request.

### 14. No `conftest.py` or `__init__.py` in backend tests

**Location:** `backend/tests/`

The tests directory has no `conftest.py` for shared fixtures and no `__init__.py`. Adding these would clean up the `sys.path` hacks and reduce duplication.

**Action:** Add `backend/tests/conftest.py` with shared fixtures and pytest path config.

### 15. `.gitignore` missing frontend-specific entries

**Location:** `.gitignore`

The gitignore is Python-focused. Frontend artifacts like `node_modules/`, `.next/`, `out/`, and `playwright-report/` are not listed. They happen to be nested under `frontend/` which has no separate `.gitignore`.

**Action:** Add `node_modules/`, `frontend/.next/`, `frontend/out/`, and `frontend/playwright-report/` to `.gitignore`.

### 16. Persistence E2E test is always skipped in normal runs

**Location:** `frontend/tests/persistence.spec.ts:3-6`

The test is gated behind `PLAYWRIGHT_NO_WEBSERVER !== "1"`, which means it only runs when explicitly configured against the Docker container. It is easy to forget this test exists.

**Action:** Document how to run it in CLAUDE.md or add a script that runs the full E2E suite against Docker.

---

## Summary

| Severity | Count |
|----------|-------|
| High     | 4     |
| Medium   | 6     |
| Low      | 6     |

### Priority order for action

1. Fix SQLite connection leak (#2)
2. Fix `_ensure_user` timestamp pollution (#3)
3. Add orphan card validation or document decision (#1)
4. Address save-on-unmount data loss risk (#4)
5. Consolidate backend test setup (#7, #11, #14)
6. Extract AI sidebar component (#10)
7. Remaining medium and low items as time permits

**Total findings: 16**
