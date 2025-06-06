# app/services/items.py

from typing import List, Optional
from sqlalchemy.orm import Session
from app import models, schemas


def get_item_by_id(db: Session, item_id: int) -> Optional[models.Item]:
    return db.query(models.Item).filter(models.Item.id == item_id).first()


def get_all_items(db: Session, skip: int = 0, limit: int = 100) -> List[models.Item]:
    return db.query(models.Item).offset(skip).limit(limit).all()


def create_item(db: Session, item: schemas.ItemCreate) -> models.Item:
    db_item = models.Item(id=getattr(item, "id", None))
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
