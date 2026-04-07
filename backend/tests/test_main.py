from fastapi.testclient import TestClient


def test_health_check(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_sample_api(client: TestClient) -> None:
    response = client.get("/api/sample")

    assert response.status_code == 200
    assert response.json() == {"message": "Backend API is reachable."}
