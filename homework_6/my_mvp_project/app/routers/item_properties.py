# app/routers/item_properties.py

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schemas, models
from .crud import get_item_property, get_item_properties, create_item_property
from app.database import get_db

router = APIRouter(
    prefix="/item_properties",
    tags=["ItemProperties"],
    )

@router.get("/", response_model=List[schemas.ItemPropertyRead])
def read_item_properties(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_item_properties(db, skip=skip, limit=limit)

@router.get("/{prop_id}", response_model=schemas.ItemPropertyRead)
def read_item_property(prop_id: int, db: Session = Depends(get_db)):
    db_prop = get_item_property(db, prop_id)
    if not db_prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"ItemProperty {prop_id} not found")
    return db_prop

@router.post("/", response_model=schemas.ItemPropertyRead, status_code=status.HTTP_201_CREATED)
def create_new_item_property(prop: schemas.ItemPropertyCreate, db: Session = Depends(get_db)):
    # Можно проверить, что item_id существует:
    existing_item = db.query(models.Item).filter(models.Item.id == prop.item_id).first()
    if not existing_item:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Item {prop.item_id} does not exist")
    return create_item_property(db, prop)