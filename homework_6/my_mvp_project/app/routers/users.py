# app/routers/users.py
"""Модуль для работы с пользователями."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .. import schemas
from ..database import get_db
from ..limiter import limiter
from . import crud

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "User not found"}},
)


@router.get("/", response_model=List[schemas.UserResponse])
@limiter.limit("100/minute")
def read_users(
    request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
) -> List[schemas.UserResponse]:
    """Получение списка пользователей."""
    logger.info(f"Запрос списка пользователей: skip={skip}, limit={limit}")
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=schemas.UserResponse)
@limiter.limit("100/minute")
def read_user(
    request: Request, user_id: int, db: Session = Depends(get_db)
) -> schemas.UserResponse:
    """Получение информации о пользователе."""
    logger.info(f"Запрос пользователя с id: {user_id}")
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        logger.warning(f"Пользователь с id {user_id} не найден.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )
    return db_user


@router.get("/{user_id}/events", response_model=List[schemas.Event])
@limiter.limit("20/minute")
async def read_user_events(
    request: Request,
    user_id: int,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
) -> List[schemas.Event]:
    """Получение событий пользователя."""
    logger.info(f"Запрос событий для пользователя с id: {user_id}")
    user = crud.get_user(db, user_id=user_id)
    if user is None:
        logger.warning(f"Запрос событий для несуществующего пользователя: {user_id}")
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    events = crud.get_user_events(db, user_id=user_id, skip=skip, limit=limit)
    logger.success(f"Найдено {len(events)} событий для пользователя {user_id}")
    return events


@router.post("/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("100/minute")
def create_user_endpoint(
    request: Request, user: schemas.UserCreate, db: Session = Depends(get_db)
) -> schemas.UserResponse:
    """Создание нового пользователя."""
    try:
        logger.info("Запрос на создание нового пользователя")
        new_user = crud.create_user(db=db, user=user)
        logger.info(f"Создан новый пользователь с id: {new_user.id}")
        return new_user
    except IntegrityError as e:
        logger.error(f"Ошибка целостности при создании пользователя: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error creating user. Please check your input data."
        )


@router.put("/{user_id}", response_model=schemas.UserResponse)
@limiter.limit("100/minute")
def update_user_endpoint(
    request: Request,
    user_id: int,
    user: schemas.UserUpdate,
    db: Session = Depends(get_db)
) -> schemas.UserResponse:
    """Обновление пользователя."""
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        logger.warning(f"Пользователь с id {user_id} не найден.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )

    try:
        updated_user = crud.update_user(db=db, user_id=user_id, user=user)
        logger.info(f"Обновлен пользователь с id: {user_id}")
        return updated_user
    except IntegrityError as e:
        logger.error(f"Ошибка целостности при обновлении пользователя: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error updating user. Please check your input data."
        )


@router.delete("/{user_id}")
@limiter.limit("100/minute")
def delete_user_endpoint(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Удаление пользователя."""
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        logger.warning(f"Пользователь с id {user_id} не найден.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )

    try:
        crud.delete_user(db=db, user_id=user_id)
        logger.info(f"Удален пользователь с id: {user_id}")
        return {"detail": f"User {user_id} deleted successfully"}
    except IntegrityError as e:
        logger.error(f"Ошибка целостности при удалении пользователя: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error deleting user. User might have related data."
        )
