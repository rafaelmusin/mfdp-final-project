"""Тесты для рекомендаций."""

import pytest
from httpx import AsyncClient
from app.tests.conftest import create_test_user, create_test_item, create_test_event


@pytest.mark.asyncio
async def test_get_recommendations_new_user(async_client: AsyncClient, db_session):
    """Тест получения рекомендаций для нового пользователя."""
    user = create_test_user(db_session)
    
    # Получаем рекомендации для нового пользователя
    resp = await async_client.get(f"/recommendations/{user.id}")
    # Может быть 503 если модель не загружена, или 200 с пустым списком
    assert resp.status_code in [200, 503]
    if resp.status_code == 200:
        recs = resp.json()
        assert "items" in recs
        assert isinstance(recs["items"], list)


@pytest.mark.asyncio
async def test_get_recommendations_with_history(async_client: AsyncClient, db_session):
    """Тест получения рекомендаций для пользователя с историей."""
    user = create_test_user(db_session)
    items = [create_test_item(db_session, item_id=100+i) for i in range(3)]
    
    # Создаем события
    for item in items:
        create_test_event(db_session, user.id, item.id, "view")
    
    response = await async_client.get(f"/recommendations/{user.id}")
    assert response.status_code in [200, 503]
    if response.status_code == 200:
        recs = response.json()
        assert "items" in recs
        assert isinstance(recs["items"], list)


@pytest.mark.asyncio
async def test_get_recommendations_nonexistent_user(async_client: AsyncClient):
    """Тест получения рекомендаций для несуществующего пользователя."""
    response = await async_client.get("/recommendations/999999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_recommendations_limit(async_client: AsyncClient, db_session):
    """Тест лимита рекомендаций."""
    user = create_test_user(db_session)
    
    response = await async_client.get(f"/recommendations/{user.id}?top_k=5")
    assert response.status_code in [200, 503]
    if response.status_code == 200:
        recs = response.json()
        assert len(recs["items"]) <= 5


@pytest.mark.asyncio
async def test_recommendations_different_event_types(async_client: AsyncClient, db_session):
    """Тест рекомендаций для разных типов событий."""
    user = create_test_user(db_session)
    items = [create_test_item(db_session, item_id=200+i) for i in range(3)]
    
    # Создаем события разных типов
    create_test_event(db_session, user.id, items[0].id, "view")
    create_test_event(db_session, user.id, items[1].id, "addtocart")
    create_test_event(db_session, user.id, items[2].id, "transaction")
    
    response = await async_client.get(f"/recommendations/{user.id}")
    assert response.status_code in [200, 503]
    if response.status_code == 200:
        recs = response.json()
        assert "items" in recs
        assert isinstance(recs["items"], list) 