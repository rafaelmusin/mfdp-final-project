# app/database.py

import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError
import app.config as settings

# (до этого стояло: from config import settings)

DATABASE_URL = settings.database_url
if not DATABASE_URL:
    raise RuntimeError(
        "ERROR: DATABASE_URL не задана в .env. "
        "В .env должно быть что-то вроде: DATABASE_URL=postgresql://user:pass@host:port/dbname"
    )

# 2) Если это SQLite (в том числе in-memory), добавляем connect_args
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# 3) Создаём SQLAlchemy Engine с учётом флага dev_mode и pool_pre_ping
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    future=True,  # рекомендуем использовать SQLAlchemy 2.0-режим
    # echo=settings.dev_mode,    # логирование SQL в зависимости от DEV_MODE
    pool_pre_ping=True,  # предотвращаем «StaleConnectionError» при перезапуске БД
)

# 4) SessionLocal — фабрика сессий (SQLAlchemy Session)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True,
)

# 5) Базовый класс для моделей
Base = declarative_base()


# 6) Функция-зависимость для FastAPI
def get_db():
    """
    1) Создаём сессию.
    2) Передаём её в endpoint.
    3) После обработки запроса закрываем сессию в finally.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    1) Ждём, пока БД станет живой.
    2) Вызываем create_all(), оборачивая в try/except — игнорируем ошибку при создании already exists.
    """
    # 1. Ожидание запуска БД
    retries = 5
    while retries > 0:
        try:
            with engine.connect():
                pass
            break
        except OperationalError:
            retries -= 1
            time.sleep(1)

    # 2. Создаём таблицы и ENUM-тип через metadata.create_all()
    try:
        Base.metadata.create_all(bind=engine, checkfirst=True)
        print("Database tables (и ENUM) созданы (если не существовали).")
    except Exception as e:
        print("Error creating tables (init_db):", e)
