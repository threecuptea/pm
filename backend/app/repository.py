import sqlite3
from contextlib import closing
from pathlib import Path

from .board_schema import BoardPayload
from .default_board import DEFAULT_BOARD


class KanbanRepository:
    def __init__(self, db_path: Path, schema_path: Path) -> None:
        self.db_path = db_path
        self.schema_path = schema_path

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as conn:
            conn.executescript(self.schema_path.read_text(encoding="utf-8"))
            self._ensure_default_user_and_board(conn)
            conn.commit()

    def get_board(self, username: str) -> BoardPayload:
        with closing(self._connect()) as conn:
            user_id = self._get_or_create_user(conn, username)
            row = conn.execute(
                "SELECT board_json FROM boards WHERE user_id = ? AND board_key = 'main'",
                (user_id,),
            ).fetchone()
            if row is None:
                board = DEFAULT_BOARD
                conn.execute(
                    "INSERT INTO boards (user_id, board_key, board_json) VALUES (?, 'main', ?)",
                    (user_id, board.model_dump_json()),
                )
                conn.commit()
                return board
            conn.commit()
            return BoardPayload.model_validate_json(row[0])

    def save_board(self, username: str, board: BoardPayload) -> BoardPayload:
        with closing(self._connect()) as conn:
            user_id = self._get_or_create_user(conn, username)
            board_json = board.model_dump_json()
            conn.execute(
                """
                INSERT INTO boards (user_id, board_key, board_json)
                VALUES (?, 'main', ?)
                ON CONFLICT(user_id, board_key)
                DO UPDATE SET board_json = excluded.board_json, updated_at = datetime('now')
                """,
                (user_id, board_json),
            )
            conn.commit()
            return board

    def _ensure_default_user_and_board(self, conn: sqlite3.Connection) -> None:
        user_id = self._get_or_create_user(conn, "user")
        row = conn.execute(
            "SELECT id FROM boards WHERE user_id = ? AND board_key = 'main'",
            (user_id,),
        ).fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO boards (user_id, board_key, board_json) VALUES (?, 'main', ?)",
                (user_id, DEFAULT_BOARD.model_dump_json()),
            )

    def _get_or_create_user(self, conn: sqlite3.Connection, username: str) -> int:
        conn.execute(
            "INSERT OR IGNORE INTO users (username) VALUES (?)",
            (username,),
        )
        row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if row is None:
            raise RuntimeError("failed to load user after upsert")
        return int(row[0])

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
