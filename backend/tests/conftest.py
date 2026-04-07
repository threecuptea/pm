from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from backend.app.main import create_app


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    app = create_app(db_path=tmp_path / "app.db")
    return TestClient(app)
