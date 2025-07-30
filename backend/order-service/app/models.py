# order-service/app/models.py
from sqlalchemy import Column, Integer, String, DECIMAL, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
from sqlalchemy.sql import func

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    # Gerçek bir uygulamada user_id string (UUID) olabilir, şimdilik integer tutuyoruz.
    user_id = Column(Integer, nullable=False)
    status = Column(String, default="pending")
    total_price = Column(DECIMAL(10, 2), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    price_per_unit = Column(DECIMAL(10, 2), nullable=False)
    order = relationship("Order", back_populates="items")