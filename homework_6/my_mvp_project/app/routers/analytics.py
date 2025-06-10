# app/routers/analytics.py
"""Модуль для аналитики и статистики."""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Request
from loguru import logger
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..limiter import limiter
from . import crud

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
    responses={404: {"description": "Analytics data not found"}},
)


@router.get("/stats", response_model=Dict[str, Any])
@limiter.limit("30/minute")
def get_system_statistics(
    request: Request, db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Получение общей статистики системы."""
    logger.info("Запрос общей статистики системы")
    stats = crud.get_system_stats(db)
    logger.info(f"Получена статистика: {stats}")
    return stats


@router.get("/popular-items", response_model=List[Dict[str, int]])
@limiter.limit("30/minute")
def get_popular_items(
    request: Request, limit: int = 10, db: Session = Depends(get_db)
) -> List[Dict[str, int]]:
    """Получение популярных товаров."""
    logger.info(f"Запрос популярных товаров, лимит: {limit}")
    popular_items = crud.get_popular_items(db, limit=limit)
    logger.info(f"Найдено {len(popular_items)} популярных товаров")
    return popular_items


@router.get("/active-users", response_model=List[Dict[str, int]])
@limiter.limit("30/minute")
def get_active_users(
    request: Request, limit: int = 10, db: Session = Depends(get_db)
) -> List[Dict[str, int]]:
    """Получение активных пользователей."""
    logger.info(f"Запрос активных пользователей, лимит: {limit}")
    active_users = crud.get_user_activity_stats(db, limit=limit)
    logger.info(f"Найдено {len(active_users)} активных пользователей")
    return active_users


@router.get("/recent-events", response_model=List[schemas.Event])
@limiter.limit("30/minute")
def get_recent_events(
    request: Request, limit: int = 20, db: Session = Depends(get_db)
) -> List[schemas.Event]:
    """Получение последних событий."""
    logger.info(f"Запрос последних событий, лимит: {limit}")
    recent_events = crud.get_recent_events(db, limit=limit)
    logger.info(f"Найдено {len(recent_events)} последних событий")
    return recent_events 