import os
from pathlib import Path

from fastapi import FastAPI
from fastapi import HTTPException, Query
from fastapi.staticfiles import StaticFiles

from .board_schema import BoardPayload
from .repository import KanbanRepository


def _default_db_path() -> Path:
    return Path(os.getenv("PM_DB_PATH", Path(__file__).resolve().parents[1] / "data" / "app.db"))


def _default_schema_path() -> Path:
    return Path(__file__).resolve().parents[1] / "db" / "schema.sql"


def create_app(db_path: Path | None = None, schema_path: Path | None = None) -> FastAPI:
    app = FastAPI(title="Project Management MVP API", version="0.1.0")

    repository = KanbanRepository(
        db_path=db_path or _default_db_path(),
        schema_path=schema_path or _default_schema_path(),
    )
    repository.initialize()

    @app.get("/api/health")
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/sample")
    def sample_api() -> dict[str, str]:
        return {"message": "Backend API is reachable."}

    @app.get("/api/board", response_model=BoardPayload)
    def get_board(username: str = Query(default="user", min_length=1)) -> BoardPayload:
        return repository.get_board(username)

    @app.put("/api/board", response_model=BoardPayload)
    def save_board(
        payload: BoardPayload,
        username: str = Query(default="user", min_length=1),
    ) -> BoardPayload:
        try:
            return repository.save_board(username, payload)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    # Part 3: serve static frontend build at '/'.
    static_dir = Path(__file__).resolve().parents[2] / "frontend_out"
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")

    return app


app = create_app()
