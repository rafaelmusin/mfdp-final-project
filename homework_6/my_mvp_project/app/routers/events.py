# app/routers/events.py
"""Модуль для работы с событиями пользователей."""

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
    prefix="/events",
    tags=["events"],
    responses={404: {"description": "Event not found"}},
)


@router.get("/", response_model=List[schemas.Event])
@limiter.limit("100/minute")
def read_events(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
) -> List[schemas.Event]:
    """Получение списка событий."""
    logger.info(f"Запрос списка событий: skip={skip}, limit={limit}")
    events = crud.get_events(db, skip=skip, limit=limit)
    return events


@router.get("/{event_id}", response_model=schemas.Event)
@limiter.limit("100/minute")
def read_event(
    request: Request, event_id: int, db: Session = Depends(get_db)
) -> schemas.Event:
    """Получение информации о событии."""
    logger.info(f"Запрос события с id: {event_id}")
    db_event = crud.get_event(db, event_id=event_id)
    if db_event is None:
        logger.warning(f"Событие с id {event_id} не найдено.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Событие не найдено"
        )
    return db_event


@router.post("/", response_model=schemas.Event, status_code=status.HTTP_201_CREATED)
@limiter.limit("100/minute")
def create_event_endpoint(
    request: Request, event: schemas.EventCreate, db: Session = Depends(get_db)
) -> schemas.Event:
    """Создание нового события."""
    try:
        logger.info(f"Запрос на создание события для пользователя {event.user_id} и товара {event.item_id}")
        new_event = crud.create_event(db=db, event=event)
        logger.info(f"Создано новое событие с id: {new_event.id}")
        return new_event
    except IntegrityError as e:
        logger.error(f"Ошибка целостности при создании события: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error creating event. Please check your input data."
        )


# Update endpoint удален - события не обновляются после создания


@router.delete("/{event_id}")
@limiter.limit("100/minute")
def delete_event_endpoint(
    request: Request, event_id: int, db: Session = Depends(get_db)
):
    """Удаление события."""
    db_event = crud.get_event(db, event_id=event_id)
    if db_event is None:
        logger.warning(f"Событие с id {event_id} не найдено.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Событие не найдено"
        )

    try:
        crud.delete_event(db=db, event_id=event_id)
        logger.info(f"Удалено событие с id: {event_id}")
        return {"detail": f"Event {event_id} deleted successfully"}
    except IntegrityError as e:
        logger.error(f"Ошибка целостности при удалении события: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error deleting event. Event might have related data."
        )
