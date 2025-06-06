# app/services/users.py

from typing import List, Optional
from sqlalchemy.orm import Session
from app import models, schemas


def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    # Если передан id, используем его; иначе пусть БД сама его сгенерирует.
    db_user = models.User(id=getattr(user, "id", None))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
