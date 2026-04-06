import sys
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.main import create_app


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    app = create_app(db_path=tmp_path / "app.db")
    return TestClient(app)


def test_health_check(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_sample_api(client: TestClient) -> None:
    response = client.get("/api/sample")

    assert response.status_code == 200
    assert response.json() == {"message": "Backend API is reachable."}
