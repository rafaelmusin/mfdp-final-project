"""Тесты для категорий."""

import pytest
from httpx import AsyncClient
from app.tests.conftest import create_test_category


@pytest.mark.asyncio
async def test_create_category(async_client: AsyncClient):
    """Тест создания категории."""
    category_data = {"name": "Test Category"}
    response = await async_client.post("/categories/", json=category_data)
    assert response.status_code == 201
    created = response.json()
    assert created["name"] == "Test Category"


@pytest.mark.asyncio  
async def test_read_category(async_client: AsyncClient, db_session):
    """Тест чтения категории."""
    test_category = create_test_category(db_session, "Read Test Category")
    
    response = await async_client.get(f"/categories/{test_category.id}")
    assert response.status_code == 200
    
    category_data = response.json()
    assert category_data["id"] == test_category.id
    assert category_data["name"] == "Read Test Category"


@pytest.mark.asyncio
async def test_list_categories(async_client: AsyncClient, db_session):
    """Тест получения списка категорий."""
    categories = [create_test_category(db_session, f"Category {i}") for i in range(3)]
    
    response = await async_client.get("/categories/")
    assert response.status_code == 200
    
    categories_data = response.json()
    assert isinstance(categories_data, list)
    assert len(categories_data) >= 3


@pytest.mark.asyncio
async def test_create_category_with_parent(async_client: AsyncClient, db_session):
    """Тест создания категории с родителем."""
    parent_category = create_test_category(db_session, "Parent Category")
    
    child_data = {
        "name": "Child Category",
        "parent_id": parent_category.id
    }
    response = await async_client.post("/categories/", json=child_data)
    assert response.status_code == 201
    
    child = response.json()
    assert child["name"] == "Child Category"
    assert child["parent_id"] == parent_category.id


@pytest.mark.asyncio
async def test_read_nonexistent_category(async_client: AsyncClient):
    """Тест чтения несуществующей категории."""
    response = await async_client.get("/categories/999999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_duplicate_category_name(async_client: AsyncClient, db_session):
    """Тест создания категории с дублирующимся именем."""
    create_test_category(db_session, "Duplicate Name")
    
    duplicate_data = {"name": "Duplicate Name"}
    response = await async_client.post("/categories/", json=duplicate_data)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_categories_pagination(async_client: AsyncClient, db_session):
    """Тест пагинации категорий."""
    categories = [create_test_category(db_session, f"Page Category {i}") for i in range(5)]
    
    response = await async_client.get("/categories/?skip=1&limit=2")
    assert response.status_code == 200
    
    categories_data = response.json()
    assert isinstance(categories_data, list)
    assert len(categories_data) <= 2
