# recommendation-service/app/models.py
from sqlalchemy import Column, Integer, ForeignKey
from .database import Base

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer)
    product_id = Column(Integer, nullable=False)