# app/services/events.py

from typing import List, Optional
from sqlalchemy.orm import Session
from app import models, schemas


def get_event_by_id(db: Session, event_id: int) -> Optional[models.Event]:
    return db.query(models.Event).filter(models.Event.id == event_id).first()


def get_all_events(db: Session, skip: int = 0, limit: int = 100) -> List[models.Event]:
    return db.query(models.Event).offset(skip).limit(limit).all()


def create_event(db: Session, event_in: schemas.EventCreate) -> models.Event:
    db_event = models.Event(
        timestamp=int(event_in.timestamp.timestamp()),
        user_id=event_in.user_id,
        item_id=event_in.item_id,
        event=event_in.event,
        transaction_id=None,  # По схеме EventCreate нет transaction_id
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event
