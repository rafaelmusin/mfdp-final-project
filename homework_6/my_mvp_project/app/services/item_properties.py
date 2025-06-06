# app/services/item_properties.py

from typing import List, Optional
from sqlalchemy.orm import Session
from app import models, schemas


def get_item_property_by_id(db: Session, prop_id: int) -> Optional[models.ItemProperty]:
    return (
        db.query(models.ItemProperty).filter(models.ItemProperty.id == prop_id).first()
    )


def get_all_item_properties(
    db: Session, skip: int = 0, limit: int = 100
) -> List[models.ItemProperty]:
    return db.query(models.ItemProperty).offset(skip).limit(limit).all()


def create_item_property(
    db: Session, prop: schemas.ItemPropertyCreate
) -> models.ItemProperty:
    db_prop = models.ItemProperty(
        timestamp=prop.timestamp,
        item_id=prop.item_id,
        property=prop.property,  # Обратите внимание: schema теперь property
        value=prop.value,
    )
    db.add(db_prop)
    db.commit()
    db.refresh(db_prop)
    return db_prop
