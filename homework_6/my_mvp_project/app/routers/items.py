# app/routers/items.py

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schemas
from app.services.items import get_item_by_id, get_all_items, create_item
from app.database import get_db

router = APIRouter(
    prefix="/items",
    tags=["Items"],
)


@router.get("/", response_model=List[schemas.ItemRead])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    1) Возвращает список всех items с учётом пагинации.
    """
    return get_all_items(db, skip=skip, limit=limit)


@router.get("/{item_id}", response_model=schemas.ItemRead)
def read_item(item_id: int, db: Session = Depends(get_db)):
    """
    1) Получаем item по ID.
    2) Если не найден — возвращаем 404.
    """
    db_item = get_item_by_id(db, item_id)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found",
        )
    return db_item


@router.post("/", response_model=schemas.ItemRead, status_code=status.HTTP_201_CREATED)
def create_new_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    """
    1) Если в теле указан id (опционально), проверяем, что такого item ещё нет.
    2) Создаём новый item.
    """
    if getattr(item, "id", None) is not None:
        existing = get_item_by_id(db, item.id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Item with id {item.id} already exists",
            )
    return create_item(db, item)
