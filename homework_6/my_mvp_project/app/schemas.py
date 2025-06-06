# app/schemas.py

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from app.models import EventTypeEnum  # для валидации EventTypeEnum


#
# Схемы для Users
#
class UserBase(BaseModel):
    pass


class UserCreate(UserBase):
    """
    Схема для создания пользователя: ID генерируется СУБД автоматически, передавать ничего не нужно.
    """

    pass


class UserRead(UserBase):
    id: int = Field(..., example=1)

    class Config:
        from_attributes = True


#
# Схемы для Items
#
class ItemCreate(BaseModel):
    """
    Схема для создания Item: ID генерируется СУБД автоматически, передавать ничего не нужно.
    """

    pass


class ItemRead(BaseModel):
    id: int = Field(..., example=42)

    class Config:
        from_attributes = True


#
# Схемы для Categories
#
class CategoryCreate(BaseModel):
    """
    Схема для создания категории: передаём только parent_id (если нужно).
    """

    parent_id: Optional[int] = Field(None, example=0)


class CategoryRead(BaseModel):
    id: int = Field(..., example=1)
    parent_id: Optional[int] = Field(None, example=0)
    # children теперь может быть либо списком CategoryRead, либо None
    children: Optional[List["CategoryRead"]] = None

    class Config:
        from_attributes = True


CategoryRead.update_forward_refs()


# ------------------------------------------------------------
#  Схемы для ItemProperty
# ------------------------------------------------------------
class ItemPropertyCreate(BaseModel):
    """
    Схема для создания ItemProperty:
    - во входящем JSON поле называется `property`
    """

    timestamp: int = Field(..., example=1617181723)
    item_id: int = Field(..., example=42)
    property: str = Field(..., example="color")
    value: str = Field(..., example="red")


class ItemPropertyRead(BaseModel):
    """
    Схема для чтения ItemProperty:
    - возвращает id, timestamp, item_id, property и value
    """

    id: int = Field(..., example=100)
    timestamp: int = Field(..., example=1617181723)
    item_id: int = Field(..., example=42)
    property: str = Field(..., example="color")
    value: str = Field(..., example="red")

    class Config:
        from_attributes = True


#
# Схемы для Event
#
class EventBase(BaseModel):
    user_id: int = Field(..., example=1)
    item_id: int = Field(..., example=42)
    event: EventTypeEnum = Field(
        ..., description="Тип события: view / addtocart / transaction"
    )
    timestamp: datetime = Field(..., example="2025-06-05T14:48:00Z")


class EventCreate(EventBase):
    """
    Схема для создания Event: передаём user_id, item_id, event, timestamp (BigInteger).
    """

    pass


class EventRead(EventBase):
    id: int = Field(..., example=10)
    created_at: datetime = Field(..., example="2025-06-05T14:48:00Z", alias="datetime")


class Config:
    from_attributes = True
    # Разрешаем возвращать поле под именем "datetime" в JSON, хотя внутри модели — created_at
    allow_population_by_field_name = True


#
# Схемы для рекомендаций
#
class RecommendationResponse(BaseModel):
    user_id: int = Field(..., example=1)
    item_id: int = Field(..., example=42)
    score: float = Field(..., example=0.75)

    class Config:
        from_attributes = True
