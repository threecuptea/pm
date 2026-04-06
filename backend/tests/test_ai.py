import sys
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

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
