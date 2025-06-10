"""Общие утилиты проекта."""

import os
import datetime
from typing import Dict


def get_db_url() -> str:
    """Получить URL базы данных."""
    return os.getenv("DATABASE_URL", "sqlite:///./test.db")


def get_temporal_features() -> Dict[str, int]:
    """Получить временные признаки для модели."""
    now = datetime.datetime.now()
    
    # Определяем, выходной ли день (суббота = 5, воскресенье = 6)
    is_weekend = 1 if now.weekday() >= 5 else 0
    
    # Определяем, вечернее ли время (после 18:00)
    is_evening = 1 if now.hour >= 18 else 0
    
    return {
        "is_weekend": is_weekend,
        "is_evening": is_evening,
    }
