import os
from pathlib import Path
import json

from fastapi import FastAPI
from fastapi import HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import httpx

from .ai import OpenRouterClient, OpenRouterError, load_openrouter_config
from .ai_chat_schema import AiChatRequest, AiChatResponse, AiStructuredOutput
from .board_schema import BoardPayload
from .repository import KanbanRepository


def _default_db_path() -> Path:
    return Path(os.getenv("PM_DB_PATH", Path(__file__).resolve().parents[1] / "data" / "app.db"))


def _default_schema_path() -> Path:
    return Path(__file__).resolve().parents[1] / "db" / "schema.sql"


def create_app(db_path: Path | None = None, schema_path: Path | None = None) -> FastAPI:
    app = FastAPI(title="Project Management MVP API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

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

    @app.get("/api/ai/test")
    def ai_test(prompt: str = Query(default="2+2", min_length=1)) -> dict[str, str]:
        try:
            config = load_openrouter_config()
        except ValueError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

        try:
            with httpx.Client(timeout=30.0) as http_client:
                client = OpenRouterClient(config=config, http_client=http_client)
                answer = client.ask(prompt)
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=502, detail=f"OpenRouter request failed: {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"OpenRouter connection failed: {exc}") from exc
        except OpenRouterError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        return {"model": config.model, "prompt": prompt, "response": answer}

    @app.post("/api/ai/chat", response_model=AiChatResponse)
    def ai_chat(
        payload: AiChatRequest,
        username: str = Query(default="user", min_length=1),
    ) -> AiChatResponse:
        board = repository.get_board(username)

        try:
            config = load_openrouter_config()
        except ValueError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

        schema = AiStructuredOutput.model_json_schema()
        board_json = json.dumps(board.model_dump(mode="json"), ensure_ascii=True)
        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": (
                    "You are a project management assistant. "
                    "Reply using the provided JSON schema only. "
                    "Use board_update only when the user clearly requests board changes. "
                    "Current board JSON: "
                    f"{board_json}"
                ),
            }
        ]
        messages.extend(
            [{"role": item.role, "content": item.content} for item in payload.history]
        )
        messages.append({"role": "user", "content": payload.question})

        try:
            with httpx.Client(timeout=30.0) as http_client:
                client = OpenRouterClient(config=config, http_client=http_client)
                raw_response = client.ask_structured(
                    messages=messages,
                    schema_name="kanban_ai_response",
                    schema=schema,
                )
            structured = AiStructuredOutput.model_validate(raw_response)
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=502, detail=f"OpenRouter request failed: {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"OpenRouter connection failed: {exc}") from exc
        except OpenRouterError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=502, detail=f"Invalid structured AI response: {exc}") from exc

        board_updated = structured.board_update is not None
        final_board = board
        if structured.board_update is not None:
            final_board = repository.save_board(username, structured.board_update)

        return AiChatResponse(
            model=config.model,
            assistant_response=structured.assistant_response,
            board_updated=board_updated,
            board=final_board,
        )

    # Part 3: serve static frontend build at '/'.
    static_dir = Path(__file__).resolve().parents[2] / "frontend_out"
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")

    return app


app = create_app()
