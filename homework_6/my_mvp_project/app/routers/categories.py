# app/routers/categories.py

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schemas, models
from .crud import get_category, get_categories, create_category
from app.database import get_db

router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
    )

@router.get("/", response_model=List[schemas.CategoryRead])
def read_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_categories(db, skip=skip, limit=limit)

@router.get("/{category_id}", response_model=schemas.CategoryRead)
def read_category(category_id: int, db: Session = Depends(get_db)):
    db_cat = get_category(db, category_id)
    if not db_cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Category {category_id} not found")
    return db_cat

@router.post("/", response_model=schemas.CategoryRead, status_code=status.HTTP_201_CREATED)
def create_new_category(category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    return create_category(db, category)