# файл: conftest.py   (должен лежать в корне проекта, рядом с папкой app/)

import os
import sys
import pytest

# ───────────────────────────────────────────────────────────────────────
# 1) Подменяем DATABASE_URL до того, как импорты что-либо «склеят» с Реальным Postgres
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

# ───────────────────────────────────────────────────────────────────────
# 2) Добавляем корень проекта в sys.path, чтобы Python точно нашёл пакет app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ───────────────────────────────────────────────────────────────────────
# 3) Импортируем базовый модуль сессий, но пока без инициализации таблиц
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool    # <–– вот он нам нужен

import app.database as _database_module
from app.database import Base, get_db

# ───────────────────────────────────────────────────────────────────────
# 4) Импортируем все модели, чтобы Base.metadata «зарегистрировала» их
import app.models

from app.main import app

# ───────────────────────────────────────────────────────────────────────
# 5) Создаём наш тестовый SQLite-engine (in-memory), но с пулом StaticPool,
#    чтобы весь «жизненный цикл» теста работал с одним и тем же соединением.
TEST_SQLALCHEMY_DATABASE_URL = os.environ["DATABASE_URL"]
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    future=True,
    )

TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


# ───────────────────────────────────────────────────────────────────────
# 6) Перезаписываем внутри модуля app.database объекты engine и SessionLocal,
#    чтобы когда наше приложение (или CRUD) вызывало get_db(),
#    оно работало именно с этим in-memory-engine.

_database_module.engine = engine
_database_module.SessionLocal = TestingSessionLocal

# ───────────────────────────────────────────────────────────────────────
# 7) Новая функция-генератор get_db, которая отдаёт сессии из нашего TestingSessionLocal
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# ───────────────────────────────────────────────────────────────────────
@pytest.fixture(scope="function", autouse=True)
def prepare_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    """
    Запускает TestClient(app), а внутри FastAPI подменяем зависимость get_db().
    """
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as tc:
        yield tc
    app.dependency_overrides.clear()