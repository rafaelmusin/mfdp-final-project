# app/schemas.py

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


#
# Схемы для Users
#
class UserBase(BaseModel):
    pass


class UserCreate(UserBase):
    id: Optional[int] = None


class UserRead(UserBase):
    id: int

    class Config:
        orm_mode = True


#
# Схемы для Items
#
class ItemBase(BaseModel):
    id: Optional[int] = None


class ItemCreate(ItemBase):
    pass


class ItemRead(ItemBase):
    id: int

    class Config:
        orm_mode = True


#
# Схемы для Categories
#
class CategoryBase(BaseModel):
    parent_id: Optional[int] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryRead(CategoryBase):
    id: int
    # children теперь может быть либо списком CategoryRead, либо None
    children: Optional[List["CategoryRead"]] = None

    class Config:
        orm_mode = True


CategoryRead.update_forward_refs()


#
# Схемы для ItemProperty
#
class ItemPropertyBase(BaseModel):
    timestamp: int
    item_id: int
    property: str
    value: str


class ItemPropertyCreate(ItemPropertyBase):
    pass


class ItemPropertyRead(ItemPropertyBase):
    id: int

    class Config:
        orm_mode = True


#
# Схемы для Event
#
class EventBase(BaseModel):
    user_id: int
    item_id: int
    event: str = Field(..., pattern="^view$|^addtocart$|^transaction$")
    timestamp: datetime


class EventCreate(EventBase):
    pass


class EventRead(EventBase):
    id: int
    datetime: datetime

    class Config:
        orm_mode = True


#
# Схемы для рекомендаций
#
class RecommendationResponse(BaseModel):
    user_id: int
    item_id: int
    score: float

    class Config:
        orm_mode = True