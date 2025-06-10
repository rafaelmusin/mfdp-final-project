"""Тесты для свойств товаров."""

import pytest
import time
from httpx import AsyncClient
from app.tests.conftest import create_test_item, create_test_item_property


@pytest.mark.asyncio
async def test_create_item_property(async_client: AsyncClient, db_session):
    """Тест создания свойства товара."""
    item = create_test_item(db_session)
    
    property_data = {
        "timestamp": int(time.time() * 1000),
        "item_id": item.id,
        "property": "color",
        "value": "red"
    }
    response = await async_client.post("/item_properties/", json=property_data)
    assert response.status_code == 201
    created = response.json()
    assert created["item_id"] == item.id
    assert created["property"] == "color"
    assert created["value"] == "red"


@pytest.mark.asyncio
async def test_read_item_property(async_client: AsyncClient, db_session):
    """Тест чтения свойства товара."""
    item = create_test_item(db_session)
    property_obj = create_test_item_property(db_session, item.id, "size", "large")
    
    response = await async_client.get(f"/item_properties/{property_obj.id}")
    assert response.status_code == 200
    
    property_data = response.json()
    assert property_data["id"] == property_obj.id
    assert property_data["item_id"] == item.id
    assert property_data["property"] == "size"
    assert property_data["value"] == "large"


@pytest.mark.asyncio
async def test_list_item_properties(async_client: AsyncClient, db_session):
    """Тест получения списка свойств товаров."""
    item = create_test_item(db_session)
    properties = [
        create_test_item_property(db_session, item.id, f"prop_{i}", f"value_{i}")
        for i in range(3)
    ]
    
    response = await async_client.get("/item_properties/")
    assert response.status_code == 200
    
    properties_data = response.json()
    assert isinstance(properties_data, list)
    assert len(properties_data) >= 3


@pytest.mark.asyncio
async def test_item_properties_different_types(async_client: AsyncClient, db_session):
    """Тест создания разных свойств товара."""
    item = create_test_item(db_session)
    
    properties_data = [
        {"property": "color", "value": "blue"},
        {"property": "size", "value": "medium"},
        {"property": "weight", "value": "1.5kg"},
        {"property": "material", "value": "cotton"}
    ]
    
    for prop_data in properties_data:
        full_data = {
            "timestamp": int(time.time() * 1000),
            "item_id": item.id,
            **prop_data
        }
        response = await async_client.post("/item_properties/", json=full_data)
        assert response.status_code == 201
        created = response.json()
        assert created["property"] == prop_data["property"]
        assert created["value"] == prop_data["value"]


@pytest.mark.asyncio
async def test_read_nonexistent_property(async_client: AsyncClient):
    """Тест чтения несуществующего свойства."""
    response = await async_client.get("/item_properties/999999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_properties_pagination(async_client: AsyncClient, db_session):
    """Тест пагинации свойств товаров."""
    item = create_test_item(db_session)
    properties = [
        create_test_item_property(db_session, item.id, f"page_prop_{i}", f"page_value_{i}")
        for i in range(5)
    ]
    
    response = await async_client.get("/item_properties/?skip=1&limit=2")
    assert response.status_code == 200
    
    properties_data = response.json()
    assert isinstance(properties_data, list)
    assert len(properties_data) <= 2
