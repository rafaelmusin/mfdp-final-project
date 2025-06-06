# app/models.py
from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    String,
    DateTime,
    Text,
    Enum,
    BigInteger,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from .database import Base


class EventTypeEnum(str, enum.Enum):
    view = "view"
    addtocart = "addtocart"
    transaction = "transaction"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    events = relationship("Event", back_populates="user", cascade="all, delete-orphan")


class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    events = relationship("Event", back_populates="item", cascade="all, delete-orphan")
    properties = relationship(
        "ItemProperty", back_populates="item", cascade="all, delete-orphan"
    )


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

    # Скалярная связь «→ родитель»
    parent = relationship(
        "Category",
        remote_side=[id],
        back_populates="children",
    )
    # Коллекционная связь «→ дети»
    children = relationship(
        "Category",
        back_populates="parent",
        cascade="all, delete-orphan",
        # по умолчанию uselist=True, поэтому children всегда будет списком
    )


class ItemProperty(Base):
    __tablename__ = "item_properties"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(BigInteger, nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    property = Column(String, nullable=False)
    value = Column(Text, nullable=False)
    item = relationship("Item", back_populates="properties")


class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(BigInteger, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    event = Column(Enum(EventTypeEnum), nullable=False)
    transaction_id = Column(String, nullable=True)
    datetime = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="events")
    item = relationship("Item", back_populates="events")
