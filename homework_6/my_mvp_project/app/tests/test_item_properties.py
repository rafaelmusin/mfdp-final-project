# app/tests/test_item_properties.py

from datetime import datetime
import pytest


@pytest.mark.parametrize("limit", [1, 5])
def test_get_item_properties_empty(client, limit):
    resp = client.get(f"/item_properties/?skip=0&limit={limit}")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_and_read_item_property(client):
    # 1) Создаём Item, чтобы получить item_id
    item_resp = client.post("/items/", json={})
    item_id = item_resp.json()["id"]

    # 2) POST /item_properties/ (отправляем property)
    now_ts = int(datetime.utcnow().timestamp())
    payload = {
        "timestamp": now_ts,
        "item_id": item_id,
        "property": "color",
        "value": "red"
        }
    resp = client.post("/item_properties/", json=payload)
    assert resp.status_code == 201

    data = resp.json()
    # Проверяем, что в ответе есть поле property (а не property)
    assert data["timestamp"] == now_ts
    assert data["item_id"] == item_id
    assert data["property"] == "color"
    assert data["value"] == "red"
    prop_id = data["id"]

    # 3) GET /item_properties/{prop_id}
    get_resp = client.get(f"/item_properties/{prop_id}")
    assert get_resp.status_code == 200
    data2 = get_resp.json()
    assert data2 == data
