# app/services/categories.py

from typing import List, Optional
from sqlalchemy.orm import Session
from app import models, schemas


def get_category_by_id(db: Session, category_id: int) -> Optional[models.Category]:
    return db.query(models.Category).filter(models.Category.id == category_id).first()


def get_all_categories(
    db: Session, skip: int = 0, limit: int = 100
) -> List[models.Category]:
    return db.query(models.Category).offset(skip).limit(limit).all()


def create_category(db: Session, category: schemas.CategoryCreate) -> models.Category:
    db_category = models.Category(parent_id=category.parent_id)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category
