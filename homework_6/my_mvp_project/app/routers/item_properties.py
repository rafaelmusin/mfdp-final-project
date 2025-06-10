# app/routers/item_properties.py
"""Модуль для работы со свойствами товаров."""

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
    prefix="/item_properties",
    tags=["item_properties"],
    responses={404: {"description": "Item property not found"}},
)


@router.get("/", response_model=List[schemas.ItemPropertyResponse])
@limiter.limit("100/minute")
def read_item_properties(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
) -> List[schemas.ItemPropertyResponse]:
    """Получение списка свойств товаров."""
    logger.info(f"Запрос списка свойств товаров: skip={skip}, limit={limit}")
    properties = crud.get_item_properties(db, skip=skip, limit=limit)
    return properties


@router.get("/{property_id}", response_model=schemas.ItemPropertyResponse)
@limiter.limit("100/minute")
def read_item_property(
    request: Request, property_id: int, db: Session = Depends(get_db)
) -> schemas.ItemPropertyResponse:
    """Получение информации о свойстве товара."""
    logger.info(f"Запрос свойства с id: {property_id}")
    db_property = crud.get_item_property(db, property_id=property_id)
    if db_property is None:
        logger.warning(f"Свойство с id {property_id} не найдено.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Свойство товара не найдено"
        )
    return db_property


@router.post("/", response_model=schemas.ItemPropertyResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("100/minute")
def create_item_property_endpoint(
    request: Request, item_property: schemas.ItemPropertyCreate, db: Session = Depends(get_db)
) -> schemas.ItemPropertyResponse:
    """Создание нового свойства товара."""
    try:
        logger.info(f"Запрос на создание свойства для товара {item_property.item_id}")
        new_property = crud.create_item_property(db=db, item_property=item_property)
        logger.info(f"Создано новое свойство с id: {new_property.id}")
        return new_property
    except IntegrityError as e:
        logger.error(f"Ошибка целостности при создании свойства: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error creating item property. Please check your input data."
        )


@router.put("/{property_id}", response_model=schemas.ItemPropertyResponse)
@limiter.limit("100/minute")
def update_item_property_endpoint(
    request: Request, property_id: int, item_property: schemas.ItemPropertyUpdate, db: Session = Depends(get_db)
) -> schemas.ItemPropertyResponse:
    """Обновление свойства товара."""
    db_property = crud.get_item_property(db, property_id=property_id)
    if db_property is None:
        logger.warning(f"Свойство с id {property_id} не найдено.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Свойство товара не найдено"
        )

    try:
        updated_property = crud.update_item_property(db=db, property_id=property_id, item_property=item_property)
        logger.info(f"Обновлено свойство с id: {property_id}")
        return updated_property
    except IntegrityError as e:
        logger.error(f"Ошибка целостности при обновлении свойства: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error updating item property. Please check your input data."
        )


@router.delete("/{property_id}")
@limiter.limit("100/minute")
def delete_item_property_endpoint(
    request: Request, property_id: int, db: Session = Depends(get_db)
):
    """Удаление свойства товара."""
    db_property = crud.get_item_property(db, property_id=property_id)
    if db_property is None:
        logger.warning(f"Свойство с id {property_id} не найдено.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Свойство товара не найдено"
        )

    try:
        crud.delete_item_property(db=db, property_id=property_id)
        logger.info(f"Удалено свойство с id: {property_id}")
        return {"detail": f"Item property {property_id} deleted successfully"}
    except IntegrityError as e:
        logger.error(f"Ошибка целостности при удалении свойства: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error deleting item property. Property might have related data."
        )
