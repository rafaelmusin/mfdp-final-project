"""Тесты для товаров."""

import pytest
from httpx import AsyncClient
from app.tests.conftest import create_test_item


@pytest.mark.asyncio
async def test_create_and_read_item(async_client: AsyncClient):
    """Тест создания и чтения товара."""
    # Создание товара
    response = await async_client.post("/items/", json={"id": 123})
    assert response.status_code == 201
    created = response.json()
    assert "id" in created

    # Получение товара
    resp2 = await async_client.get(f"/items/{created['id']}")
    assert resp2.status_code == 200
    single = resp2.json()
    assert single["id"] == created["id"]


@pytest.mark.asyncio
async def test_get_nonexistent_item(async_client: AsyncClient):
    """Тест получения несуществующего товара."""
    resp = await async_client.get("/items/9999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_items(async_client: AsyncClient, db_session):
    """Тест получения списка товаров."""
    # Создаем несколько товаров
    items = [create_test_item(db_session) for _ in range(3)]
    
    # Запрашиваем список товаров
    response = await async_client.get("/items/")
    assert response.status_code == 200
    
    items_data = response.json()
    assert isinstance(items_data, list)
    assert len(items_data) >= 3


@pytest.mark.asyncio
async def test_list_items_with_pagination(async_client: AsyncClient, db_session):
    """Тест получения списка товаров с пагинацией."""
    # Создаем несколько товаров
    items = [create_test_item(db_session) for _ in range(5)]
    
    # Запрашиваем с пагинацией
    response = await async_client.get("/items/?skip=1&limit=2")
    assert response.status_code == 200
    
    items_data = response.json()
    assert isinstance(items_data, list)
    assert len(items_data) <= 2
