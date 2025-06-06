# app/routers/crud.py

from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from app import models, schemas


#
# CRUD для User
#
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    # Если передан id, используем его; иначе пусть БД сама его сгенерирует.
    db_user = models.User(id=user.id)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

#
# CRUD для Item
#
def get_item(db: Session, item_id: int):
    return db.query(models.Item).filter(models.Item.id == item_id).first()

def get_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Item).offset(skip).limit(limit).all()

def create_item(db: Session, item: schemas.ItemCreate):
    db_item = models.Item(id=item.id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

#
# CRUD для Category
#
def get_category(db: Session, category_id: int):
    return db.query(models.Category).filter(models.Category.id == category_id).first()

def get_categories(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Category).offset(skip).limit(limit).all()

def create_category(db: Session, category: schemas.CategoryCreate):
    db_category = models.Category(parent_id=category.parent_id)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

#
# CRUD для ItemProperty
#
def get_item_property(db: Session, prop_id: int):
    return db.query(models.ItemProperty).filter(models.ItemProperty.id == prop_id).first()

def get_item_properties(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.ItemProperty).offset(skip).limit(limit).all()

def create_item_property(db: Session, prop: schemas.ItemPropertyCreate):
    db_prop = models.ItemProperty(
        timestamp=prop.timestamp,
        item_id=prop.item_id,
        property=prop.property,
        value=prop.value
        )
    db.add(db_prop)
    db.commit()
    db.refresh(db_prop)
    return db_prop

#
# CRUD для Event
#
def get_event(db: Session, event_id: int):
    return db.query(models.Event).filter(models.Event.id == event_id).first()

def get_events(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Event).offset(skip).limit(limit).all()

def create_event(db: Session, event: schemas.EventCreate):
    db_event = models.Event(
        timestamp=int(event.timestamp.timestamp()),
        user_id=event.user_id,
        item_id=event.item_id,
        event=event.event,
        transaction_id=None  # пока нет transaction_id в схеме создания
        )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event