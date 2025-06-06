# tests/test_items.py

def test_create_and_read_item(client):
    # POST /items/
    response = client.post("/items/", json={})
    assert response.status_code == 201
    created = response.json()
    assert "id" in created

    # GET /items/
    resp2 = client.get("/items/")
    assert resp2.status_code == 200
    items = resp2.json()
    assert any(i["id"] == created["id"] for i in items)

    # GET /items/{id}
    resp3 = client.get(f"/items/{created['id']}")
    assert resp3.status_code == 200
    single = resp3.json()
    assert single["id"] == created["id"]


def test_get_nonexistent_item(client):
    resp = client.get("/items/9999")
    assert resp.status_code == 404
