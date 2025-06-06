# app/routers/events.py

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schemas, models
from app.services.events import get_event_by_id, get_all_events, create_event
from app.database import get_db

router = APIRouter(
    prefix="/events",
    tags=["Events"],
)


@router.get("/", response_model=List[schemas.EventRead])
def read_events(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    1) Возвращает все события (Events) с пагинацией.
    """
    return get_all_events(db, skip=skip, limit=limit)


@router.get("/{event_id}", response_model=schemas.EventRead)
def read_event(event_id: int, db: Session = Depends(get_db)):
    """
    1) Получаем Event по ID.
    2) Если не найдено — возвращаем 404.
    """
    db_evt = get_event_by_id(db, event_id)
    if not db_evt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {event_id} not found",
        )
    return db_evt


@router.post("/", response_model=schemas.EventRead, status_code=status.HTTP_201_CREATED)
def create_new_event(evt: schemas.EventCreate, db: Session = Depends(get_db)):
    """
    1) Проверяем существование user_id и item_id.
    2) Создаём новое Event.
    """
    if not db.query(models.User).filter(models.User.id == evt.user_id).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User {evt.user_id} does not exist",
        )
    if not db.query(models.Item).filter(models.Item.id == evt.item_id).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Item {evt.item_id} does not exist",
        )
    return create_event(db, evt)
