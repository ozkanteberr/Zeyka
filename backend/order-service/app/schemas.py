from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import List

# Order Item Schemas
class OrderItemBase(BaseModel):
    product_id: int
    quantity: int

class OrderItemCreate(OrderItemBase):
    pass

class OrderItem(OrderItemBase):
    id: int
    price_per_unit: Decimal

    class Config:
        from_attributes = True

# Order Schemas
class OrderBase(BaseModel):
    pass

class OrderCreate(OrderBase):
    items: List[OrderItemCreate]

class Order(OrderBase):
    id: int
    user_id: int
    status: str
    total_price: Decimal
    created_at: datetime
    items: List[OrderItem] = []

    class Config:
        from_attributes = True