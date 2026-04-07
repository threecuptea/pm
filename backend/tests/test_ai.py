import json
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from backend.app.ai import OpenRouterClient, OpenRouterConfig
from backend.app.main import create_app


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


class _FakeHTTPClient:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def post(self, *_args, **_kwargs) -> _FakeResponse:
        return _FakeResponse(self.payload)


def test_openrouter_client_parses_response() -> None:
    client = OpenRouterClient(
        config=OpenRouterConfig(api_key="test-key"),
        http_client=_FakeHTTPClient(
            {"choices": [{"message": {"content": "4"}}]}
        ),
    )

    assert client.ask("2+2") == "4"


def test_openrouter_client_parses_structured_response() -> None:
    client = OpenRouterClient(
        config=OpenRouterConfig(api_key="test-key"),
        http_client=_FakeHTTPClient(
            {
                "choices": [
                    {
                        "message": {
                            "content": '{"assistant_response":"Done","board_update":null}'
                        }
                    }
                ]
            }
        ),
    )

    result = client.ask_structured(
        messages=[{"role": "user", "content": "hi"}],
        schema_name="kanban_ai_response",
        schema={"type": "object"},
    )

    assert result == {"assistant_response": "Done", "board_update": None}


def test_ai_test_route_missing_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    app = create_app(db_path=tmp_path / "app.db")
    client = TestClient(app)

    response = client.get("/api/ai/test")

    assert response.status_code == 503
    assert response.json()["detail"] == "OPENROUTER_API_KEY is missing"


def test_ai_test_route_handles_upstream_http_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    import httpx

    class _RaisingClient:
        def __enter__(self) -> "_RaisingClient":
            return self

        def __exit__(self, exc_type, exc, tb) -> bool:
            return False

        def post(self, *_args, **_kwargs):
            raise httpx.ConnectError("boom")

    monkeypatch.setattr("backend.app.main.httpx.Client", lambda *args, **kwargs: _RaisingClient())

    app = create_app(db_path=tmp_path / "app.db")
    client = TestClient(app)

    response = client.get("/api/ai/test")

    assert response.status_code == 502
    assert "OpenRouter connection failed" in response.json()["detail"]


def test_ai_chat_route_returns_message_without_board_update(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    class _RouteClient:
        def __enter__(self) -> "_RouteClient":
            return self

        def __exit__(self, exc_type, exc, tb) -> bool:
            return False

        def post(self, *_args, **_kwargs) -> _FakeResponse:
            return _FakeResponse(
                {
                    "choices": [
                        {
                            "message": {
                                "content": '{"assistant_response":"No board changes needed.","board_update":null}'
                            }
                        }
                    ]
                }
            )

    monkeypatch.setattr("backend.app.main.httpx.Client", lambda *args, **kwargs: _RouteClient())

    app = create_app(db_path=tmp_path / "app.db")
    client = TestClient(app)

    response = client.post(
        "/api/ai/chat",
        json={
            "question": "What should I do next?",
            "history": [{"role": "user", "content": "I am blocked."}],
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["assistant_response"] == "No board changes needed."
    assert payload["board_updated"] is False
    assert len(payload["board"]["columns"]) == 5


def test_ai_chat_route_persists_board_update(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    app = create_app(db_path=tmp_path / "app.db")
    client = TestClient(app)

    board = client.get("/api/board").json()
    board["columns"][0]["title"] = "AI Backlog"
    ai_payload = {"assistant_response": "Renamed backlog.", "board_update": board}

    class _RouteClient:
        def __enter__(self) -> "_RouteClient":
            return self

        def __exit__(self, exc_type, exc, tb) -> bool:
            return False

        def post(self, *_args, **_kwargs) -> _FakeResponse:
            return _FakeResponse(
                {
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(ai_payload)
                            }
                        }
                    ]
                }
            )

    monkeypatch.setattr("backend.app.main.httpx.Client", lambda *args, **kwargs: _RouteClient())

    response = client.post(
        "/api/ai/chat",
        json={"question": "Rename backlog to AI Backlog.", "history": []},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["assistant_response"] == "Renamed backlog."
    assert payload["board_updated"] is True
    assert payload["board"]["columns"][0]["title"] == "AI Backlog"

    board_response = client.get("/api/board")
    assert board_response.status_code == 200
    assert board_response.json()["columns"][0]["title"] == "AI Backlog"


def test_ai_chat_route_rejects_invalid_structured_payload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    class _RouteClient:
        def __enter__(self) -> "_RouteClient":
            return self

        def __exit__(self, exc_type, exc, tb) -> bool:
            return False

        def post(self, *_args, **_kwargs) -> _FakeResponse:
            return _FakeResponse(
                {
                    "choices": [
                        {
                            "message": {
                                "content": '{"board_update":null}'
                            }
                        }
                    ]
                }
            )

    monkeypatch.setattr("backend.app.main.httpx.Client", lambda *args, **kwargs: _RouteClient())

    app = create_app(db_path=tmp_path / "app.db")
    client = TestClient(app)

    response = client.post(
        "/api/ai/chat",
        json={"question": "hello", "history": []},
    )

    assert response.status_code == 502
    assert "Invalid structured AI response" in response.json()["detail"]
