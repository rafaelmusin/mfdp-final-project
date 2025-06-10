# app/database.py
"""Настройка базы данных."""

import os
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import logging

from app.common_utils import get_db_url

logger = logging.getLogger(__name__)

# Настройка движка базы данных
SQLALCHEMY_DATABASE_URL = get_db_url()

# Создаем движок
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    # Для SQLite используем специальные настройки
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    # Для других БД (PostgreSQL, MySQL)
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Сессия для работы с БД
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()


def get_db() -> Session:
    """Создание сессии базы данных."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_db():
    """Инициализация базы данных."""
    from app.models import User, Item, Category, Event, ItemProperty
    
    logger.info("Создание таблиц...")
    Base.metadata.create_all(bind=engine)
    logger.info("Таблицы созданы")
    
    # Задержка для стабилизации
    await asyncio.sleep(1)
