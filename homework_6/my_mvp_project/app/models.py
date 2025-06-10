# app/models.py

import enum

from sqlalchemy import (
    BigInteger,
    DateTime,
    String,
    Column,
    Integer,
    ForeignKey,
    Index,
    Text,
    Float,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


class EventTypeEnum(str, enum.Enum):
    """Типы событий пользователей."""
    view = "view"
    addtocart = "addtocart"
    transaction = "transaction"
    rate = "rate"


class User(Base):
    """Модель пользователя системы."""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    events = relationship("Event", back_populates="user")
    __table_args__ = ()


class Item(Base):
    """Модель товара."""
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Связи
    events = relationship("Event", back_populates="item")
    properties = relationship(
        "ItemProperty", back_populates="item", cascade="all, delete-orphan"
    )


class Category(Base):
    """Модель категории товаров с иерархией."""
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, unique=True, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)

    # Связи для иерархии
    parent = relationship(
        "Category",
        remote_side=[id],
        back_populates="children",
    )
    children = relationship(
        "Category",
        back_populates="parent",
        cascade="all, delete-orphan",
    )

    # Ограничения
    __table_args__ = (
        CheckConstraint('length(name) >= 2', name='check_category_name_length'),
        CheckConstraint('length(name) <= 50', name='check_category_name_max_length'),
        CheckConstraint('length(description) <= 500', name='check_category_description_length'),
    )


class ItemProperty(Base):
    """Модель свойства товара."""
    __tablename__ = "item_properties"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(BigInteger, nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False, index=True)
    property = Column(String, nullable=False, index=True)
    value = Column(Text, nullable=False)
    item = relationship("Item", back_populates="properties")

    # Индексы и ограничения
    __table_args__ = (
        Index("ix_item_properties_item_id_property", "item_id", "property"),
        CheckConstraint('length(property) >= 1', name='check_property_name_length'),
        CheckConstraint('length(property) <= 50', name='check_property_name_max_length'),
        CheckConstraint('length(value) >= 1', name='check_property_value_length'),
        CheckConstraint('length(value) <= 1000', name='check_property_value_max_length'),
        CheckConstraint('timestamp >= 0', name='check_property_timestamp_positive'),
    )


class Event(Base):
    """Модель события пользователя."""
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(BigInteger, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)
    transaction_id = Column(String, nullable=True)
    datetime = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="events")
    item = relationship("Item", back_populates="events")

    # Индексы для быстрых запросов
    __table_args__ = (
        Index("ix_events_user_id_event", "user_id", "event_type"),
        Index("ix_events_item_id_event", "item_id", "event_type"),
        CheckConstraint('timestamp >= 0', name='check_event_timestamp_positive'),
    )
