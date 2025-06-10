# app/routers/crud.py
"""CRUD операции для работы с базой данных.

Этот модуль содержит функции для выполнения основных операций с базой данных:
- Create: создание новых записей
- Read: получение существующих записей
- Update: обновление записей (не реализовано в текущей версии)
- Delete: удаление записей (не реализовано в текущей версии)

Поддерживаемые сущности:
- User: пользователи системы
- Item: товары
- Category: категории товаров
- ItemProperty: свойства товаров
- Event: события взаимодействия пользователей с товарами

Особенности:
- Все операции чтения поддерживают пагинацию
- Максимальный размер страницы ограничен 1000 записей
- При создании записей ID генерируются автоматически
- Все операции выполняются в рамках транзакций
"""

from typing import List, Optional, Union, Tuple
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc, and_, or_, case
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import IntegrityError

from .. import models, schemas

# CRUD операции для сущностей приложения
# Организовано по типу сущности для лучшей читаемости


# CRUD для User
def get_user(db: Session, user_id: int):
    """Получить пользователя по ID."""
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    """Получить список пользователей."""
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    """Создать нового пользователя."""
    db_user = models.User()
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_id: int):
    """Обновить пользователя."""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        # У пользователя нет обновляемых полей, кроме ID
        db.commit()
        db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int):
    """Удалить пользователя."""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user


# CRUD для Item
def get_item(db: Session, item_id: int):
    """Получить товар по ID."""
    return db.query(models.Item).filter(models.Item.id == item_id).first()


def get_items(db: Session, skip: int = 0, limit: int = 100):
    """Получить список товаров."""
    return db.query(models.Item).offset(skip).limit(limit).all()


def create_item(db: Session, item: schemas.ItemCreate):
    """Создать новый товар."""
    # Если ID указан в схеме, используем его, иначе автогенерация
    if hasattr(item, 'id') and item.id is not None:
        db_item = models.Item(id=item.id)
    else:
        db_item = models.Item()
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def update_item(db: Session, item_id: int):
    """Обновить товар."""
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if db_item:
        # У товара нет обновляемых полей, кроме ID
        db.commit()
        db.refresh(db_item)
    return db_item


def delete_item(db: Session, item_id: int):
    """Удалить товар."""
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if db_item:
        db.delete(db_item)
        db.commit()
    return db_item


# CRUD для Category
def get_category(db: Session, category_id: int):
    """Получить категорию по ID."""
    return db.query(models.Category).filter(models.Category.id == category_id).first()


def get_categories(db: Session, skip: int = 0, limit: int = 100):
    """Получить список категорий."""
    return db.query(models.Category).offset(skip).limit(limit).all()


def create_category(db: Session, category: schemas.CategoryCreate):
    """Создать новую категорию."""
    db_category = models.Category(
        name=category.name,
        description=category.description,
        parent_id=category.parent_id
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def update_category(db: Session, category_id: int, category: schemas.CategoryUpdate):
    """Обновить категорию."""
    db_category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if db_category:
        if category.name is not None:
            db_category.name = category.name
        if category.description is not None:
            db_category.description = category.description
        if category.parent_id is not None:
            db_category.parent_id = category.parent_id
        db.commit()
        db.refresh(db_category)
    return db_category


def delete_category(db: Session, category_id: int):
    """Удалить категорию."""
    db_category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if db_category:
        db.delete(db_category)
        db.commit()
    return db_category


# CRUD для ItemProperty
def get_item_property(db: Session, property_id: int):
    """Получить свойство товара по ID."""
    return db.query(models.ItemProperty).filter(models.ItemProperty.id == property_id).first()


def get_item_properties(db: Session, skip: int = 0, limit: int = 100):
    """Получить список свойств товаров."""
    return db.query(models.ItemProperty).offset(skip).limit(limit).all()


def create_item_property(db: Session, item_property: schemas.ItemPropertyCreate):
    """Создать новое свойство товара."""
    db_property = models.ItemProperty(
        timestamp=item_property.timestamp,
        item_id=item_property.item_id,
        property=item_property.property,
        value=item_property.value
    )
    db.add(db_property)
    db.commit()
    db.refresh(db_property)
    return db_property


def update_item_property(db: Session, property_id: int, item_property: schemas.ItemPropertyUpdate):
    """Обновить свойство товара."""
    db_property = db.query(models.ItemProperty).filter(models.ItemProperty.id == property_id).first()
    if db_property:
        if item_property.property is not None:
            db_property.property = item_property.property
        if item_property.value is not None:
            db_property.value = item_property.value
        db.commit()
        db.refresh(db_property)
    return db_property


def delete_item_property(db: Session, property_id: int):
    """Удалить свойство товара."""
    db_property = db.query(models.ItemProperty).filter(models.ItemProperty.id == property_id).first()
    if db_property:
        db.delete(db_property)
        db.commit()
    return db_property


# CRUD для Event
def get_event(db: Session, event_id: int):
    """Получить событие по ID."""
    return db.query(models.Event).filter(models.Event.id == event_id).first()


def get_events(db: Session, skip: int = 0, limit: int = 100):
    """Получить список событий."""
    return db.query(models.Event).offset(skip).limit(limit).all()


def get_user_events(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """Получить события пользователя."""
    return db.query(models.Event).filter(models.Event.user_id == user_id).offset(skip).limit(limit).all()


def create_event(db: Session, event: schemas.EventCreate):
    """Создать новое событие."""
    db_event = models.Event(
        user_id=event.user_id,
        item_id=event.item_id,
        event_type=event.event_type,
        timestamp=event.timestamp or int(datetime.now().timestamp() * 1000),
        transaction_id=event.transaction_id
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def update_event(db: Session, event_id: int, event_type=None, transaction_id=None):
    """Обновить событие."""
    db_event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if db_event:
        if event_type is not None:
            db_event.event_type = event_type
        if transaction_id is not None:
            db_event.transaction_id = transaction_id
        db.commit()
        db.refresh(db_event)
    return db_event


def delete_event(db: Session, event_id: int):
    """Удалить событие."""
    db_event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if db_event:
        db.delete(db_event)
        db.commit()
        return True
    return False


# === Функции для аналитики ===

def get_system_stats(db: Session):
    """Получить общую статистику системы."""
    from sqlalchemy import func
    
    total_users = db.query(models.User).count()
    total_items = db.query(models.Item).count()
    total_events = db.query(models.Event).count()
    total_categories = db.query(models.Category).count()
    
    # Статистика по типам событий
    event_stats = db.query(
        models.Event.event_type,
        func.count(models.Event.id).label('count')
    ).group_by(models.Event.event_type).all()
    
    return {
        "total_users": total_users,
        "total_items": total_items,
        "total_events": total_events,
        "total_categories": total_categories,
        "event_types": [{"type": stat.event_type, "count": stat.count} for stat in event_stats]
    }


def get_popular_items(db: Session, limit: int = 10):
    """Получить популярные товары по количеству событий."""
    from sqlalchemy import func, desc
    
    popular_items = db.query(
        models.Item.id,
        func.count(models.Event.id).label('event_count')
    ).join(models.Event).group_by(models.Item.id).order_by(
        desc(func.count(models.Event.id))
    ).limit(limit).all()
    
    return [{"item_id": item.id, "event_count": item.event_count} for item in popular_items]


def get_user_activity_stats(db: Session, limit: int = 10):
    """Получить статистику активности пользователей."""
    from sqlalchemy import func, desc
    
    active_users = db.query(
        models.User.id,
        func.count(models.Event.id).label('event_count')
    ).join(models.Event).group_by(models.User.id).order_by(
        desc(func.count(models.Event.id))
    ).limit(limit).all()
    
    return [{"user_id": user.id, "event_count": user.event_count} for user in active_users]


def get_recent_events(db: Session, limit: int = 20):
    """Получить последние события."""
    from sqlalchemy import desc
    
    recent_events = db.query(models.Event).order_by(desc(models.Event.timestamp)).limit(limit).all()
    
    return recent_events


# === Функции для каталога товаров ===

def search_items(db: Session, search_query: str = "", category_id: int = None, 
                limit: int = 20, offset: int = 0):
    """Поиск товаров с фильтрацией."""
    from sqlalchemy import or_, func
    
    query = db.query(models.Item)
    
    # Поиск по названию (если есть поле name в Item)
    if search_query:
        # Поиск по ID товара (так как у нас нет поля name)
        try:
            item_id = int(search_query)
            query = query.filter(models.Item.id == item_id)
        except ValueError:
            # Если не число, ищем среди свойств товара
            query = query.join(models.ItemProperty).filter(
                or_(
                    models.ItemProperty.property.ilike(f"%{search_query}%"),
                    models.ItemProperty.value.ilike(f"%{search_query}%")
                )
            ).distinct()
    
    # Пропускаем фильтр по категории, так как товары не привязаны к категориям
    # if category_id:
    #     query = query.filter(models.Item.category_id == category_id)
    
    # Общее количество для пагинации
    total = query.count()
    
    # Применяем лимит и оффсет
    items = query.offset(offset).limit(limit).all()
    
    return items, total


def get_item_with_details(db: Session, item_id: int):
    """Получить товар с детальной информацией."""
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        return None
    
    # Получаем свойства товара
    properties = db.query(models.ItemProperty).filter(models.ItemProperty.item_id == item_id).all()
    
    # Пропускаем получение категории, так как товары не привязаны к категориям
    category = None
    
    # Статистика по товару
    from sqlalchemy import func
    stats = db.query(
        models.Event.event_type,
        func.count(models.Event.id).label('count')
    ).filter(models.Event.item_id == item_id).group_by(models.Event.event_type).all()
    
    return {
        "item": {"id": item.id, "created_at": str(item.created_at)},
        "properties": [{"property": prop.property, "value": prop.value} for prop in properties],
        "category": category,
        "event_stats": [{"type": stat.event_type, "count": stat.count} for stat in stats]
    }


def get_categories_with_counts(db: Session):
    """Получить категории с количеством товаров (просто все доступные категории)."""
    categories = db.query(models.Category).all()
    
    # Так как товары не привязаны к категориям, показываем все категории с нулевым счетчиком
    return [{"id": cat.id, "name": cat.name, "item_count": 0} for cat in categories]


def get_random_items(db: Session, limit: int = 12):
    """Получить случайные товары для витрины."""
    from sqlalchemy import func
    
    items = db.query(models.Item).order_by(func.random()).limit(limit).all()
    return items
