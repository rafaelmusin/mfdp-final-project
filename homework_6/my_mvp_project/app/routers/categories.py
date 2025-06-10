# app/routers/categories.py
"""Модуль для работы с категориями товаров."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .. import schemas, models
from ..database import get_db
from ..limiter import limiter
from . import crud

router = APIRouter(
    prefix="/categories",
    tags=["categories"],
    responses={404: {"description": "Category not found"}},
)


@router.get("/", response_model=List[schemas.Category])
@limiter.limit("100/minute")
def read_categories(
    request: Request, skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
) -> List[schemas.Category]:
    """Получение списка категорий."""
    logger.info(f"Запрос списка категорий: skip={skip}, limit={limit}")
    categories = crud.get_categories(db, skip=skip, limit=limit)
    return categories


@router.get("/{category_id}", response_model=schemas.Category)
@limiter.limit("100/minute")
def read_category(
    request: Request, category_id: int, db: Session = Depends(get_db)
) -> schemas.Category:
    """Получение информации о категории."""
    logger.info(f"Запрос категории с id: {category_id}")
    db_category = crud.get_category(db, category_id=category_id)
    if db_category is None:
        logger.warning(f"Категория с id {category_id} не найдена.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Категория не найдена"
        )
    return db_category


@router.post("/", response_model=schemas.Category, status_code=status.HTTP_201_CREATED)
@limiter.limit("100/minute")
def create_category_endpoint(
    request: Request, category: schemas.CategoryCreate, db: Session = Depends(get_db)
) -> schemas.Category:
    """Создание новой категории."""
    logger.info(f"Запрос на создание категории с именем: {category.name}")
    # Проверка уникальности имени категории
    existing_category = db.query(models.Category).filter(models.Category.name == category.name).first()
    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with name '{category.name}' already exists"
        )
    try:
        new_category = crud.create_category(db=db, category=category)
        logger.info(f"Создана новая категория с id: {new_category.id}")
        return new_category
    except IntegrityError as e:
        logger.error(f"Ошибка целостности при создании категории: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error creating category. Please check your input data."
        )


@router.put("/{category_id}", response_model=schemas.Category)
@limiter.limit("100/minute")
def update_category_endpoint(
    request: Request, category_id: int, category: schemas.CategoryUpdate, db: Session = Depends(get_db)
) -> schemas.Category:
    """Обновление категории."""
    # Проверка существования категории
    existing_category = crud.get_category(db, category_id=category_id)
    if existing_category is None:
        logger.warning(f"Категория с id {category_id} не найдена.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Категория не найдена"
        )

    # Проверка уникальности нового имени
    if category.name:
        name_exists = db.query(models.Category).filter(
            models.Category.name == category.name,
            models.Category.id != category_id
        ).first()
        if name_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with name '{category.name}' already exists"
            )

    try:
        return crud.update_category(db=db, category_id=category_id, category=category)
    except IntegrityError as e:
        logger.error(f"Ошибка целостности при обновлении категории: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error updating category. Please check your input data."
        )


@router.delete("/{category_id}")
@limiter.limit("100/minute")
def delete_category_endpoint(
    request: Request, category_id: int, db: Session = Depends(get_db)
):
    """Удаление категории."""
    # Проверка существования категории
    category = crud.get_category(db, category_id=category_id)
    if category is None:
        logger.warning(f"Категория с id {category_id} не найдена.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Категория не найдена"
        )

    # Проверка наличия связанных товаров
    if category.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category with associated items"
        )

    try:
        crud.delete_category(db=db, category_id=category_id)
        return {"message": f"Category {category_id} deleted successfully"}
    except IntegrityError as e:
        logger.error(f"Ошибка целостности при удалении категории: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error deleting category. Please check if it has any dependencies."
        )
