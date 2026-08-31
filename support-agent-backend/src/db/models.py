from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, relationship

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    orders = relationship("Order", back_populates="owner")

class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, index=True)  # e.g., "ORD-1001"
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    item_name = Column(String, nullable=True)
    status = Column(String, nullable=False)  # "Processing", "Shipped", "delivered"
    tracking_number = Column(String, nullable=True)
    total_amount = Column(Float, nullable=False)
    status_description = Column(Text, nullable=True)
    shipping_address = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="orders")

class Policy(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    content = Column(Text, nullable=False)