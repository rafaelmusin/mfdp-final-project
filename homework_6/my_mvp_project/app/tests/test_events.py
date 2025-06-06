# tests/test_events.py

from datetime import datetime


def test_create_and_read_event(client):
    # Нужно сначала создать user и item
    user_resp = client.post("/users/", json={})
    user_id = user_resp.json()["id"]

    item_resp = client.post("/items/", json={})
    item_id = item_resp.json()["id"]

    # POST /events/
    # Timestamp в формате ISO (Pydantic превратит в datetime)
    now_iso = datetime.utcnow().isoformat()
    payload = {
        "user_id": user_id,
        "item_id": item_id,
        "event": "view",
        "timestamp": now_iso
        }
    resp = client.post("/events/", json=payload)
    assert resp.status_code == 201
    evt = resp.json()
    assert evt["user_id"] == user_id
    assert evt["item_id"] == item_id
    assert evt["event"] == "view"
    assert "id" in evt

    # GET /events/
    list_resp = client.get("/events/")
    assert list_resp.status_code == 200
    evts = list_resp.json()
    assert any(e["id"] == evt["id"] for e in evts)

    # GET /events/{id}
    single_resp = client.get(f"/events/{evt['id']}")
    assert single_resp.status_code == 200
    single = single_resp.json()
    assert single["id"] == evt["id"]


def test_create_event_invalid_user_or_item(client):
    # Случай: несуществующий user
    now_iso = datetime.utcnow().isoformat()
    payload1 = {
        "user_id": 9999,
        "item_id": 1,  # даже если item существует или нет, сначала пропадёт на user
        "event": "view",
        "timestamp": now_iso
        }
    resp1 = client.post("/events/", json=payload1)
    assert resp1.status_code == 400

    # Сначала создать пользователя
    user_resp = client.post("/users/", json={})
    user_id = user_resp.json()["id"]

    # Запрос с несуществующим item
    payload2 = {
        "user_id": user_id,
        "item_id": 9999,
        "event": "view",
        "timestamp": now_iso
        }
    resp2 = client.post("/events/", json=payload2)
    assert resp2.status_code == 400


def test_get_nonexistent_event(client):
    resp = client.get("/events/9999")
    assert resp.status_code == 404
