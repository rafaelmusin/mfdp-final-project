# app/routers/item_properties.py

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schemas, models
from app.services.item_properties import (
    get_item_property_by_id,
    get_all_item_properties,
    create_item_property,
)
from app.database import get_db

router = APIRouter(
    prefix="/item_properties",
    tags=["ItemProperties"],
)


@router.get("/", response_model=List[schemas.ItemPropertyRead])
def read_item_properties(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    """
    1) Возвращает список всех свойств товаров с пагинацией.
    """
    return get_all_item_properties(db, skip=skip, limit=limit)


@router.get("/{prop_id}", response_model=schemas.ItemPropertyRead)
def read_item_property(prop_id: int, db: Session = Depends(get_db)):
    """
    1) Получаем ItemProperty по ID.
    2) Если не найдено — возвращаем 404.
    """
    db_prop = get_item_property_by_id(db, prop_id)
    if not db_prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ItemProperty {prop_id} not found",
        )
    return db_prop


@router.post(
    "/", response_model=schemas.ItemPropertyRead, status_code=status.HTTP_201_CREATED
)
def create_new_item_property(
    prop: schemas.ItemPropertyCreate, db: Session = Depends(get_db)
):
    """
    1) Перед созданием проверяем, что item_id существует.
    2) Создаём ItemProperty.
    """
    existing_item = db.query(models.Item).filter(models.Item.id == prop.item_id).first()
    if not existing_item:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Item {prop.item_id} does not exist",
        )
    return create_item_property(db, prop)
