import os
from pathlib import Path
import json

from fastapi import FastAPI
from fastapi import HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import httpx

from backend.app.ai import OpenRouterClient, OpenRouterError, load_openrouter_config
from backend.app.ai_chat_schema import AiChatRequest, AiChatResponse, AiStructuredOutput
from backend.app.board_schema import BoardPayload
from backend.app.repository import KanbanRepository


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
    async def ai_test(prompt: str = Query(default="2+2", min_length=1)) -> dict[str, str]:
        try:
            config = load_openrouter_config()
        except ValueError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

        try:
            async with httpx.AsyncClient(timeout=30.0) as http_client:
                client = OpenRouterClient(config=config, http_client=http_client)
                answer = await client.ask_async(prompt)
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=502, detail=f"OpenRouter request failed: {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"OpenRouter connection failed: {exc}") from exc
        except OpenRouterError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        return {"model": config.model, "prompt": prompt, "response": answer}

    @app.post("/api/ai/chat", response_model=AiChatResponse)
    async def ai_chat(
        payload: AiChatRequest,
        username: str = Query(default="user", min_length=1),
    ) -> AiChatResponse:
        board = repository.get_board(username)

        try:
            config = load_openrouter_config()
        except ValueError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

        schema = AiStructuredOutput.model_json_schema()
        # Try model_dump_json(ensure_ascii=True) but it does not work why
        board_json = json.dumps(board.model_dump(mode="json"), ensure_ascii=True)
        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": (
                    "You are a project management assistant. "
                    "Your response MUST be a JSON object with exactly these fields:\n"
                    "- \"assistant_response\": a human-readable string explaining what you did\n"
                    "- \"board_update\": null if no board changes, or the COMPLETE updated board object\n\n"
                    "CRITICAL RULES for board_update:\n"
                    "- It must be a COMPLETE copy of the current board with your changes applied.\n"
                    "- Every column must have all fields: id, title, cardIds.\n"
                    "- Every card id in any column's cardIds MUST have a matching entry in the cards map.\n"
                    "- The cards map must include ALL cards with all fields: id, title, details.\n"
                    "- Do NOT omit fields. Do NOT return a partial board.\n\n"
                    "Current board JSON:\n"
                    f"{board_json}"
                ),
            }
        ]
        messages.extend(
            [{"role": item.role, "content": item.content} for item in payload.history]
        )
        messages.append({"role": "user", "content": payload.question})

        try:
            # we can use httpx.AsyncClient here to make the request asynchronously
            async with httpx.AsyncClient(timeout=30.0) as http_client:
                client = OpenRouterClient(config=config, http_client=http_client)
                raw_response = await client.ask_structured_async(
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
