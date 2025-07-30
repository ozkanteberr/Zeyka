from sqlalchemy.orm import Session
from . import models, schemas
from decimal import Decimal

def create_order(db: Session, order: schemas.OrderCreate, user_id: int):
    # Bu basit versiyonda, ürün fiyatlarını doğrulamak için product-service ile konuşmuyoruz.
    total_price = sum([Decimal('10.0') * item.quantity for item in order.items])

    db_order = models.Order(user_id=user_id, total_price=total_price)
    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    for item in order.items:
        db_item = models.OrderItem(
            **item.model_dump(),
            order_id=db_order.id,
            price_per_unit=Decimal('10.0') # Fiyatı varsayımsal olarak ekliyoruz
        )
        db.add(db_item)

    db.commit()
    db.refresh(db_order)
    return db_order