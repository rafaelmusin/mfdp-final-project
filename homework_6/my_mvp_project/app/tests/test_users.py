"""Тесты для пользователей."""

import pytest
from httpx import AsyncClient
from app.tests.conftest import create_test_user


@pytest.mark.asyncio
async def test_create_user(async_client: AsyncClient):
    """Тест создания пользователя."""
    response = await async_client.post("/users/", json={})
    assert response.status_code == 201
    user = response.json()
    assert "id" in user
    assert "created_at" in user


@pytest.mark.asyncio
async def test_read_user(async_client: AsyncClient, db_session):
    """Тест чтения пользователя."""
    # Создаем пользователя через базу данных
    test_user = create_test_user(db_session)
    
    # Запрашиваем пользователя через API
    response = await async_client.get(f"/users/{test_user.id}")
    assert response.status_code == 200
    
    user_data = response.json()
    assert user_data["id"] == test_user.id
    assert "created_at" in user_data


@pytest.mark.asyncio
async def test_read_nonexistent_user(async_client: AsyncClient):
    """Тест чтения несуществующего пользователя."""
    response = await async_client.get("/users/999999")
    assert response.status_code == 404
    assert "не найден" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_users(async_client: AsyncClient, db_session):
    """Тест получения списка пользователей."""
    # Создаем несколько пользователей
    users = [create_test_user(db_session) for _ in range(3)]
    
    # Запрашиваем список пользователей
    response = await async_client.get("/users/")
    assert response.status_code == 200
    
    users_data = response.json()
    assert isinstance(users_data, list)
    assert len(users_data) >= 3


@pytest.mark.asyncio
async def test_list_users_with_pagination(async_client: AsyncClient, db_session):
    """Тест получения списка пользователей с пагинацией."""
    # Создаем несколько пользователей
    users = [create_test_user(db_session) for _ in range(5)]
    
    # Запрашиваем с пагинацией
    response = await async_client.get("/users/?skip=1&limit=2")
    assert response.status_code == 200
    
    users_data = response.json()
    assert isinstance(users_data, list)
    assert len(users_data) <= 2
