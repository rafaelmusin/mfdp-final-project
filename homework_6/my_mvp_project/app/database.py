# файл: app/database.py

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 1) БЕЗ жёсткого fallback-а. Берём DATABASE_URL только из окружения.
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "Переменная окружения DATABASE_URL не задана. "
        "Задайте её, например, через docker-compose или в CI/CD."
        )

# 2) Если это SQLite (в том числе in-memory), добавляем connect_args
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# 3) Создаём SQLAlchemy Engine
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    future=True,    # рекомендуем использовать SQLAlchemy 2.0-режим
    echo=False,     # при необходимости можно переключить в True для отладки
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
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()