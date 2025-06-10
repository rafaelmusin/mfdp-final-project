# app/routers/items.py
"""Модуль для работы с товарами."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .. import schemas
from ..database import get_db
from ..limiter import limiter
from . import crud

router = APIRouter(
    prefix="/items",
    tags=["items"],
    responses={404: {"description": "Item not found"}},
)


@router.get("/", response_model=List[schemas.Item])
@limiter.limit("100/minute")
def read_items(
    request: Request, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100), db: Session = Depends(get_db)
) -> List[schemas.Item]:
    """Получение списка товаров."""
    logger.info(f"Запрос списка товаров: skip={skip}, limit={limit}")
    items = crud.get_items(db, skip=skip, limit=limit)
    return items


@router.get("/{item_id}", response_model=schemas.Item)
@limiter.limit("100/minute")
def read_item(
    request: Request, item_id: int, db: Session = Depends(get_db)
) -> schemas.Item:
    """Получение информации о товаре."""
    logger.info(f"Запрос товара с id: {item_id}")
    db_item = crud.get_item(db, item_id=item_id)
    if db_item is None:
        logger.warning(f"Товар с id {item_id} не найден.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Товар не найден"
        )
    return db_item


@router.post("/", response_model=schemas.Item, status_code=status.HTTP_201_CREATED)
@limiter.limit("100/minute")
def create_item_endpoint(
    request: Request, item: schemas.ItemCreate, db: Session = Depends(get_db)
) -> schemas.Item:
    """Создание нового товара."""
    try:
        logger.info("Запрос на создание товара")
        new_item = crud.create_item(db=db, item=item)
        logger.info(f"Создан новый товар с id: {new_item.id}")
        return new_item
    except IntegrityError as e:
        logger.error(f"Ошибка целостности при создании товара: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error creating item. Please check your input data."
        )


# Update endpoint удален - товары не обновляются после создания


@router.delete("/{item_id}")
@limiter.limit("100/minute")
def delete_item_endpoint(
    request: Request, item_id: int, db: Session = Depends(get_db)
):
    """Удаление товара."""
    db_item = crud.get_item(db, item_id=item_id)
    if db_item is None:
        logger.warning(f"Товар с id {item_id} не найден.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Товар не найден"
        )

    try:
        crud.delete_item(db=db, item_id=item_id)
        logger.info(f"Удален товар с id: {item_id}")
        return {"detail": f"Item {item_id} deleted successfully"}
    except IntegrityError as e:
        logger.error(f"Ошибка целостности при удалении товара: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error deleting item. Item might have related data."
        )
