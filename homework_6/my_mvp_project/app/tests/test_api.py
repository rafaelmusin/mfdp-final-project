# tests/test_api.py

import pytest
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

# Локальный SQLite для тестов. Можно PostgreSQL, но для CI удобнее SQLite in-memory.
SQLALCHEMY_DATABASE_URL = "sqlite+pysqlite:///:memory:"

engine_test = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine_test, autoflush=False, autocommit=False)

# Подменяем зависимость get_db на тестовую сессию
@pytest.fixture(scope="session", autouse=True)
def prepare_database():
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
async def client(db_session, monkeypatch):
    # Подменяем get_db, чтобы FastAPI использовал sqlite in-memory
    async def override_get_db():
        try:
            yield db_session
        finally:
            pass

    monkeypatch.setattr("app.database.get_db", override_get_db)
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_create_and_read_user(client):
    # 1. Создаем пользователя
    response = await client.post("/users/", json={"id": 1})
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1

    # 2. Читаем список пользователей
    response = await client.get("/users/")
    assert response.status_code == 200
    users = response.json()
    assert isinstance(users, list)
    assert users[0]["id"] == 1

    # 3. Читаем по id
    response = await client.get("/users/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1


@pytest.mark.asyncio
async def test_create_item_and_read(client):
    response = await client.post("/items/", json={})
    assert response.status_code == 201
    item = response.json()
    assert "id" in item

    # проверить, что в списке ровно 1 элемент и его id совпадает
    response = await client.get("/items/")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["id"] == item["id"]


@pytest.mark.asyncio
async def test_create_and_read_category(client):
    # без parent
    response = await client.post("/categories/", json={"parent_id": None})
    assert response.status_code == 201
    cat = response.json()
    assert "id" in cat

    # дочерняя категория
    response = await client.post("/categories/", json={"parent_id": cat["id"]})
    assert response.status_code == 201
    child = response.json()
    assert child["parent_id"] == cat["id"]

    response = await client.get(f"/categories/{cat['id']}")
    assert response.status_code == 200
    assert response.json()["children"][0]["id"] == child["id"]


@pytest.mark.asyncio
async def test_create_and_read_property_and_event(client):
    # Сначала нужен Item
    it = (await client.post("/items/", json={})).json()

    # Создаем property
    response = await client.post("/item_properties/", json={
        "timestamp": 1234567890,
        "item_id": it["id"],
        "property": "color",
        "value": "red"
        })
    assert response.status_code == 201
    prop = response.json()
    assert prop["item_id"] == it["id"]
    assert prop["property"] == "color"

    # Создаем User
    usr = (await client.post("/users/", json={"id": 2})).json()

    # Событие (время передаём строкой ISO)
    from datetime import datetime
    ts = datetime.utcnow().isoformat()
    response = await client.post("/events/", json={
        "user_id": usr["id"],
        "item_id": it["id"],
        "event": "view",
        "timestamp": ts
        })
    assert response.status_code == 201
    evt = response.json()
    assert evt["user_id"] == usr["id"]
    assert evt["item_id"] == it["id"]

    # Список событий
    response = await client.get("/events/")
    assert response.status_code == 200
    evts = response.json()
    assert len(evts) == 1