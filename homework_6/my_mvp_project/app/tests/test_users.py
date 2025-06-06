# tests/test_users.py

def test_create_and_read_user(client):
    # POST /users/ — создаём пользователя (без указания id)
    response = client.post("/users/", json={})
    assert response.status_code == 201
    created = response.json()
    assert "id" in created

    # GET /users/ — список
    resp2 = client.get("/users/")
    assert resp2.status_code == 200
    users = resp2.json()
    assert any(u["id"] == created["id"] for u in users)

    # GET /users/{id}
    resp3 = client.get(f"/users/{created['id']}")
    assert resp3.status_code == 200
    single = resp3.json()
    assert single["id"] == created["id"]


def test_get_nonexistent_user(client):
    resp = client.get("/users/9999")
    assert resp.status_code == 404
