from fastapi.testclient import TestClient


def test_get_board_returns_default_for_user(client: TestClient) -> None:
    response = client.get("/api/board")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["columns"]) == 5
    assert "card-1" in payload["cards"]


def test_put_board_persists_updates(client: TestClient) -> None:
    board = client.get("/api/board").json()
    board["columns"][0]["title"] = "Updated Backlog"

    save_response = client.put("/api/board", json=board)
    assert save_response.status_code == 200
    assert save_response.json()["columns"][0]["title"] == "Updated Backlog"

    read_response = client.get("/api/board")
    assert read_response.status_code == 200
    assert read_response.json()["columns"][0]["title"] == "Updated Backlog"


def test_put_board_rejects_invalid_reference(client: TestClient) -> None:
    board = client.get("/api/board").json()
    board["columns"][0]["cardIds"].append("missing-card-id")

    response = client.put("/api/board", json=board)

    assert response.status_code == 422
