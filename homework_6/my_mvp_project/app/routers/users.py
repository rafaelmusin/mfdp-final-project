# app/routers/users.py

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schemas, models
from .crud import get_user, get_users, create_user
from app.database import get_db

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    )

@router.get("/", response_model=List[schemas.UserRead])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_users(db, skip=skip, limit=limit)

@router.get("/{user_id}", response_model=schemas.UserRead)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User {user_id} not found")
    return db_user

@router.post("/", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
def create_new_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Опционально: проверить, что пользователь с таким id ещё не существует
    if user.id is not None:
        existing = get_user(db, user.id)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"User with id {user.id} already exists")
    return create_user(db, user)