# app/routers/catalog.py
"""Модуль для каталога товаров."""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Request, Query, HTTPException
from loguru import logger
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..limiter import limiter
from . import crud

router = APIRouter(
    prefix="/catalog",
    tags=["catalog"],
    responses={404: {"description": "Item not found"}},
)


@router.get("/search", response_model=Dict[str, Any])
@limiter.limit("60/minute")
def search_items(
    request: Request,
    q: Optional[str] = Query(None, description="Поисковый запрос"),
    category_id: Optional[int] = Query(None, description="ID категории"),
    limit: int = Query(20, ge=1, le=100, description="Количество товаров на странице"),
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Поиск товаров с фильтрацией и пагинацией."""
    logger.info(f"Поиск товаров: query='{q}', category={category_id}, limit={limit}, offset={offset}")
    
    items, total = crud.search_items(
        db=db, 
        search_query=q or "", 
        category_id=category_id,
        limit=limit, 
        offset=offset
    )
    
    logger.info(f"Найдено товаров: {len(items)} из {total}")
    
    return {
        "items": [{"id": item.id, "created_at": str(item.created_at)} for item in items],
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total
    }


@router.get("/categories", response_model=List[Dict[str, Any]])
@limiter.limit("30/minute")
def get_categories(
    request: Request, db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Получение категорий с количеством товаров."""
    logger.info("Запрос категорий с подсчетом товаров")
    categories = crud.get_categories_with_counts(db)
    logger.info(f"Получено категорий: {len(categories)}")
    return categories


@router.get("/featured", response_model=List[Dict[str, Any]])
@limiter.limit("30/minute")
def get_featured_items(
    request: Request, 
    limit: int = Query(12, ge=1, le=50, description="Количество товаров"),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Получение рекомендуемых товаров для витрины."""
    logger.info(f"Запрос рекомендуемых товаров: limit={limit}")
    items = crud.get_random_items(db, limit=limit)
    logger.info(f"Получено товаров для витрины: {len(items)}")
    return [{"id": item.id, "created_at": str(item.created_at)} for item in items]


@router.get("/items/{item_id}", response_model=Dict[str, Any])
@limiter.limit("60/minute")
def get_item_details(
    request: Request, 
    item_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Получение детальной информации о товаре."""
    logger.info(f"Запрос детальной информации о товаре: {item_id}")
    
    item_details = crud.get_item_with_details(db, item_id)
    if not item_details:
        logger.warning(f"Товар {item_id} не найден")
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    logger.info(f"Получена информация о товаре {item_id}")
    return item_details


@router.post("/items/{item_id}/event")
@limiter.limit("30/minute")
def create_item_event(
    request: Request,
    item_id: int,
    event_data: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """Создание события взаимодействия с товаром."""
    logger.info(f"Создание события для товара {item_id}: {event_data}")
    
    # Проверяем существование товара
    item = crud.get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    # Создаем событие (предполагаем, что пользователь передается в event_data)
    try:
        event = crud.create_event(db, event_data)
        logger.info(f"Событие создано: {event.id}")
        return {"message": "Событие успешно создано", "event_id": str(event.id)}
    except Exception as e:
        logger.error(f"Ошибка создания события: {e}")
        raise HTTPException(status_code=400, detail="Ошибка создания события") 