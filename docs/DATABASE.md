# Database design (Part 5)

## Goals

- SQLite database file created automatically if missing.
- Support multiple users in schema, while MVP uses one hardcoded login.
- One Kanban board per user for MVP (`board_key = "main"`).
- Store complete board state as JSON for simple persistence and easy restore.

## Schema

### `users`

- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `username` TEXT NOT NULL UNIQUE
- `created_at` TEXT NOT NULL DEFAULT `datetime('now')`
- `updated_at` TEXT NOT NULL DEFAULT `datetime('now')`

Why:
- Future-safe for multi-user support.
- `username` unique lookup for auth/user mapping.

### `boards`

- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `user_id` INTEGER NOT NULL REFERENCES `users(id)` ON DELETE CASCADE
- `board_key` TEXT NOT NULL DEFAULT `main`
- `board_json` TEXT NOT NULL
- `created_at` TEXT NOT NULL DEFAULT `datetime('now')`
- `updated_at` TEXT NOT NULL DEFAULT `datetime('now')`
- UNIQUE(`user_id`, `board_key`)

Indexes:
- `idx_boards_user_id` on `boards(user_id)`

Why:
- Keeps MVP to one board per user by enforcing one `(user_id, board_key)` row.
- Allows future expansion to additional boards per user by varying `board_key`.

## JSON payload format

`board_json` stores the full board state as JSON string with this shape:

```json
{
  "columns": [
    {
      "id": "col-backlog",
      "title": "Backlog",
      "cardIds": ["card-1", "card-2"]
    }
  ],
  "cards": {
    "card-1": {
      "id": "card-1",
      "title": "Example card",
      "details": "Example details"
    }
  }
}
```

Validation rules for Part 6 implementation:
- `columns` required array.
- `cards` required object map keyed by card id.
- Each column id unique.
- Each `cardIds` entry must exist in `cards`.

## Bootstrapping approach

At backend startup (or first repository call):

1. Ensure parent directory for DB file exists.
2. Open SQLite connection to target DB path.
3. Execute SQL in `backend/db/schema.sql`.
4. Ensure default user row exists for username `user`.
5. Ensure default board row exists for that user with initial Kanban JSON.

This keeps first run deterministic and allows local development without manual setup.

## File locations

- Schema SQL: `backend/db/schema.sql`
- Database file target for MVP: `backend/data/app.db` (to be created in Part 6)

## Test plan (for Part 6)

Automated:
- Creating repository on empty directory creates DB file and tables.
- Default user and default `main` board are present after bootstrap.
- Read/write cycle returns valid JSON and persists updates.
- Invalid JSON payload is rejected by service validation.

Manual:
- Inspect DB with sqlite tool and verify `users` + `boards` rows.
- Restart app and verify persisted board state remains intact.

## Open questions for sign-off

1. Keep `board_json` as full snapshot only (current proposal), or track change history now?
2. Keep timestamps as SQLite `TEXT` in UTC via `datetime('now')` (current proposal), or prefer integer unix epoch?
3. Confirm default board key `main` naming.
