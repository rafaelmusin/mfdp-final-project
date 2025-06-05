# tests/test_item_properties.py

from datetime import datetime

def test_create_and_read_item_property(client):
    # Сначала нужно создать товар, чтобы получить item_id
    item_resp = client.post("/items/", json={})
    item_id = item_resp.json()["id"]

    # POST /item_properties/
    now_ts = int(datetime.utcnow().timestamp())
    payload = {
        "timestamp": now_ts,
        "item_id": item_id,
        "property": "color",
        "value": "red"
        }
    resp = client.post("/item_properties/", json=payload)
    assert resp.status_code == 201
    prop = resp.json()
    assert prop["item_id"] == item_id
    assert prop["property"] == "color"
    assert prop["value"] == "red"

    # GET /item_properties/
    list_resp = client.get("/item_properties/")
    assert list_resp.status_code == 200
    props = list_resp.json()
    assert any(p["id"] == prop["id"] for p in props)

    # GET /item_properties/{id}
    single_resp = client.get(f"/item_properties/{prop['id']}")
    assert single_resp.status_code == 200
    single = single_resp.json()
    assert single["id"] == prop["id"]

def test_create_item_property_invalid_item(client):
    # Если item_id не существует, должен быть 400
    now_ts = int(datetime.utcnow().timestamp())
    payload = {
        "timestamp": now_ts,
        "item_id": 9999,
        "property": "weight",
        "value": "1kg"
        }
    resp = client.post("/item_properties/", json=payload)
    assert resp.status_code == 400