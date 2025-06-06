# app/routers/users.py

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schemas
from app.services.users import get_user_by_id, get_all_users, create_user
from app.database import get_db

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get("/", response_model=List[schemas.UserRead])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    1) Возвращает список всех пользователей с учётом пагинации (skip, limit).
    """
    return get_all_users(db, skip=skip, limit=limit)


@router.get("/{user_id}", response_model=schemas.UserRead)
def read_user(user_id: int, db: Session = Depends(get_db)):
    """
    1) Получаем user по ID.
    2) Если не найден — возвращаем 404.
    """
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )
    return db_user


@router.post("/", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
def create_new_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    1) Если в теле указали id (опционально), проверяем, что такого user ещё нет.
    2) Создаём нового user.
    """
    if getattr(user, "id", None) is not None:
        existing = get_user_by_id(db, user.id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with id {user.id} already exists",
            )
    return create_user(db, user)
