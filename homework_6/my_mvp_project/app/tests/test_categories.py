# tests/test_categories.py

def test_create_and_read_category(client):
    # POST /categories/ без parent_id
    response = client.post("/categories/", json={})
    assert response.status_code == 201
    created = response.json()
    assert "id" in created
    assert created.get("parent_id") is None

    # Создадим подкатегорию (parent_id = только что созданный)
    response2 = client.post("/categories/", json={"parent_id": created["id"]})
    assert response2.status_code == 201
    child = response2.json()
    assert child["parent_id"] == created["id"]

    # GET /categories/
    resp_list = client.get("/categories/")
    assert resp_list.status_code == 200
    cats = resp_list.json()
    # Должны быть хотя бы две: родитель и ребёнок
    assert any(c["id"] == created["id"] for c in cats)
    assert any(c["id"] == child["id"] for c in cats)

    # GET /categories/{id}
    resp_single = client.get(f"/categories/{child['id']}")
    assert resp_single.status_code == 200
    single = resp_single.json()
    assert single["id"] == child["id"]
    assert single["parent_id"] == created["id"]

def test_get_nonexistent_category(client):
    resp = client.get("/categories/9999")
    assert resp.status_code == 404