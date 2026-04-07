import sqlite3
from pathlib import Path

from backend.app.repository import KanbanRepository


def test_initialize_creates_db_and_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "app.db"
    schema_path = Path(__file__).resolve().parents[1] / "db" / "schema.sql"

    repository = KanbanRepository(db_path=db_path, schema_path=schema_path)
    repository.initialize()

    assert db_path.exists()

    with sqlite3.connect(db_path) as conn:
        users_table = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'users'"
        ).fetchone()
        boards_table = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'boards'"
        ).fetchone()
        default_user = conn.execute(
            "SELECT username FROM users WHERE username = 'user'"
        ).fetchone()
        default_board = conn.execute(
            "SELECT board_key FROM boards WHERE board_key = 'main'"
        ).fetchone()

    assert users_table is not None
    assert boards_table is not None
    assert default_user is not None
    assert default_board is not None
