"""Конфигурация для тестов."""

import os
import tempfile
from typing import AsyncGenerator, Generator
import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app


# Создаем временную базу данных для тестов
@pytest.fixture(scope="session")
def temp_db():
    """Создать временную базу данных для тестов."""
    # Создаем временный файл для SQLite
    temp_fd, temp_path = tempfile.mkstemp(suffix=".db")
    os.close(temp_fd)  # Закрываем дескриптор, SQLite создаст свой
    
    # Создаем движок для временной базы
    engine = create_engine(f"sqlite:///{temp_path}", connect_args={"check_same_thread": False})
    
    # Создаем все таблицы
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Очистка после тестов
    try:
        os.unlink(temp_path)
    except (FileNotFoundError, PermissionError):
        pass


@pytest.fixture
def db_session(temp_db):
    """Создать сессию базы данных для тестов."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=temp_db)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def override_get_db(db_session):
    """Переопределить зависимость get_db для тестов."""
    def _override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def async_client(override_get_db) -> AsyncGenerator[AsyncClient, None]:
    """Создать асинхронный HTTP клиент для тестов."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="session")
def event_loop():
    """Создать event loop для тестов."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


def create_test_user(db_session):
    """Создать тестового пользователя."""
    from app.models import User
    user = User()
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def create_test_item(db_session, item_id=None):
    """Создать тестовый товар."""
    from app.models import Item
    if item_id:
        item = Item(id=item_id)
    else:
        item = Item()
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item


def create_test_category(db_session, name="Test Category", parent_id=None):
    """Создать тестовую категорию."""
    from app.models import Category
    category = Category(name=name, parent_id=parent_id)
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


def create_test_event(db_session, user_id, item_id, event_type="view"):
    """Создать тестовое событие."""
    from app.models import Event
    import time
    
    event = Event(
        user_id=user_id,
        item_id=item_id,
        event_type=event_type,
        timestamp=int(time.time() * 1000)
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    return event


def create_test_item_property(db_session, item_id, property_name="test_property", value="test_value"):
    """Создать тестовое свойство товара."""
    from app.models import ItemProperty
    import time
    
    property_obj = ItemProperty(
        item_id=item_id,
        property=property_name,
        value=value,
        timestamp=int(time.time() * 1000)
    )
    db_session.add(property_obj)
    db_session.commit()
    db_session.refresh(property_obj)
    return property_obj
