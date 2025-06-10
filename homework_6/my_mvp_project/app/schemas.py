# app/schemas.py
"""Схемы для валидации данных API."""

import re
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, validator, constr

from app.models import EventTypeEnum


# Схемы для Users
class UserBase(BaseModel):
    """Базовая схема для пользователя (только id)."""
    pass


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    pass


class UserResponse(UserBase):
    id: int
    created_at: datetime
    model_config = {"from_attributes": True}


class User(UserBase):
    id: int
    created_at: datetime
    model_config = {"from_attributes": True}


# Схемы для Categories
class CategoryBase(BaseModel):
    """Базовая схема для категории.
    
    Attributes:
        name (str): Название категории (от 1 до 100 символов)
        parent_id (Optional[int]): ID родительской категории. None для корневых категорий
    """

    name: constr(min_length=1, max_length=100)
    parent_id: Optional[int] = None
    description: Optional[str] = Field(None, max_length=500, description="Описание категории")

    @validator('name')
    def name_not_empty(cls, v):
        """Проверяет, что название категории не состоит только из пробелов."""
        if not v.strip():
            raise ValueError('Название категории не может быть пустым')
        return v.strip()

    @validator('name')
    def name_must_be_valid(cls, v):
        """Проверка корректности названия категории."""
        if not re.match(r'^[a-zA-Zа-яА-Я0-9\s\-_]+$', v):
            raise ValueError('Название категории может содержать только буквы, цифры, пробелы, дефисы и подчеркивания')
        return v


class CategoryCreate(CategoryBase):
    """Схема для создания категории.
    
    Наследуется от CategoryBase и не добавляет новых полей,
    так как все необходимые поля уже определены в базовой схеме.
    """

    pass


class CategoryUpdate(BaseModel):
    """Схема для обновления категории."""
    name: Optional[str] = Field(None, min_length=2, max_length=50, description="Название категории")
    description: Optional[str] = Field(None, max_length=500, description="Описание категории")

    @validator('name')
    def name_must_be_valid(cls, v):
        """Проверка корректности названия категории."""
        if v is not None and not re.match(r'^[a-zA-Zа-яА-Я0-9\s\-_]+$', v):
            raise ValueError('Название категории может содержать только буквы, цифры, пробелы, дефисы и подчеркивания')
        return v


class CategoryResponse(CategoryBase):
    """Схема для ответа с информацией о категории."""
    id: int
    model_config = {"from_attributes": True}


class Category(CategoryBase):
    """Схема категории с ID.
    
    Attributes:
        id (int): Уникальный идентификатор категории
        name (str): Название категории
        parent_id (Optional[int]): ID родительской категории
    """

    id: int
    model_config = {"from_attributes": True}


# Схемы для ItemProperty
class ItemPropertyBase(BaseModel):
    """Базовая схема для свойства товара.
    
    Attributes:
        property (str): Название свойства (от 1 до 50 символов)
        value (str): Значение свойства (от 1 до 200 символов)
    """

    property: constr(min_length=1, max_length=50)
    value: constr(min_length=1, max_length=1000)
    timestamp: int = Field(..., description="Временная метка")

    @validator('property', 'value')
    def field_not_empty(cls, v):
        """Проверяет, что поле не состоит только из пробелов."""
        if not v.strip():
            raise ValueError('Поле не может быть пустым')
        return v.strip()

    @validator('timestamp')
    def timestamp_must_be_valid(cls, v):
        """Проверка корректности временной метки."""
        current_time = int(datetime.now().timestamp() * 1000)
        if v < 0:
            raise ValueError('Временная метка не может быть отрицательной')
        if v > current_time + 86400000:  # 24 часа в будущем
            raise ValueError('Временная метка не может быть более чем на 24 часа в будущем')
        return v


class ItemPropertyCreate(ItemPropertyBase):
    """Схема для создания свойства товара.
    
    Attributes:
        item_id (int): ID товара, к которому относится свойство
        timestamp (int): Временная метка создания свойства в миллисекундах
        property (str): Название свойства
        value (str): Значение свойства
    """

    item_id: int = Field(..., gt=0, description="ID товара")


class ItemPropertyUpdate(BaseModel):
    """Схема для обновления свойства товара."""
    property: Optional[str] = Field(None, min_length=1, max_length=50, description="Название свойства")
    value: Optional[str] = Field(None, min_length=1, max_length=1000, description="Значение свойства")
    timestamp: Optional[int] = Field(None, description="Временная метка")

    @validator('timestamp')
    def timestamp_must_be_valid(cls, v):
        """Проверка корректности временной метки."""
        if v is not None:
            current_time = int(datetime.now().timestamp() * 1000)
            if v < 0:
                raise ValueError('Временная метка не может быть отрицательной')
            if v > current_time + 86400000:  # 24 часа в будущем
                raise ValueError('Временная метка не может быть более чем на 24 часа в будущем')
        return v


class ItemPropertyResponse(ItemPropertyBase):
    """Схема для ответа с информацией о свойстве товара."""
    id: int
    item_id: int
    model_config = {"from_attributes": True}


# Схемы для Items
class ItemBase(BaseModel):
    """Базовая схема для товара.
    
    В исходных данных товар содержит только ID,
    вся остальная информация хранится в properties.
    """
    pass


class ItemCreate(ItemBase):
    """Схема для создания товара.
    
    Товар создается только с ID, который будет взят из CSV данных.
    """
    pass


class ItemUpdate(BaseModel):
    """Схема для обновления товара."""
    pass


class ItemResponse(ItemBase):
    """Схема для ответа с информацией о товаре."""
    id: int
    created_at: datetime
    model_config = {"from_attributes": True}


class Item(BaseModel):
    id: int
    model_config = {"from_attributes": True}


# Схемы для Event
class EventBase(BaseModel):
    """Базовая схема для события.
    
    Attributes:
        user_id (int): ID пользователя
        item_id (int): ID товара
        event_type (EventTypeEnum): Тип события (view, addtocart, transaction)
    """

    user_id: int = Field(..., gt=0, description="ID пользователя")
    item_id: int = Field(..., gt=0, description="ID товара")
    event_type: EventTypeEnum
    timestamp: Optional[int] = Field(None, description="Временная метка")

    @validator('timestamp')
    def timestamp_must_be_valid(cls, v):
        """Проверка корректности временной метки."""
        current_time = int(datetime.now().timestamp() * 1000)
        if v < 0:
            raise ValueError('Временная метка не может быть отрицательной')
        if v > current_time + 86400000:  # 24 часа в будущем
            raise ValueError('Временная метка не может быть более чем на 24 часа в будущем')
        return v


class EventCreate(EventBase):
    """Схема для создания события.
    
    Attributes:
        user_id (int): ID пользователя
        item_id (int): ID товара
        event_type (EventTypeEnum): Тип события
        timestamp (int): Временная метка события в миллисекундах
        transaction_id (Optional[str]): ID транзакции (для событий покупки)
    """
    transaction_id: Optional[str] = Field(None, description="ID транзакции")


class EventResponse(EventBase):
    """Схема для ответа с информацией о событии."""
    id: int
    user: UserResponse
    item: ItemResponse
    model_config = {"from_attributes": True}


class Event(EventBase):
    """Схема события с ID и временной меткой.
    
    Attributes:
        id (int): Уникальный идентификатор события
        user_id (int): ID пользователя
        item_id (int): ID товара
        event_type (EventTypeEnum): Тип события
        timestamp (int): Временная метка события в миллисекундах
    """

    id: int
    model_config = {"from_attributes": True}


# Схемы для рекомендаций
class RecommendedItem(BaseModel):
    """Схема рекомендуемого товара.
    
    Attributes:
        id (int): ID рекомендуемого товара
        name (Optional[str]): Название товара (опционально)
        score (float): Оценка релевантности рекомендации (от 0 до 1)
    """

    id: int
    name: Optional[str] = None
    score: float = Field(ge=0.0, le=1.0)


class RecommendedItems(BaseModel):
    """Схема списка рекомендуемых товаров.
    
    Attributes:
        items (List[RecommendedItem]): Список рекомендуемых товаров с их оценками
    """

    items: List[RecommendedItem]
