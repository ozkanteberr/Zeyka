# recommendation-service/app/crud.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from . import models
from collections import Counter

def get_recommendations(db: Session, product_id: int, limit: int = 5):
    # 1. Adım: Verilen ürünün bulunduğu tüm siparişlerin ID'lerini bul.
    orders_with_product = db.query(models.OrderItem.order_id).filter(models.OrderItem.product_id == product_id).distinct()
    order_ids = [order.order_id for order in orders_with_product]

    if not order_ids:
        return []

    # 2. Adım: Bu siparişlerde bulunan diğer tüm ürünleri bul.
    co_purchased_items = db.query(models.OrderItem).filter(
        models.OrderItem.order_id.in_(order_ids),
        models.OrderItem.product_id != product_id
    ).all()

    if not co_purchased_items:
        return []

    # 3. Adım: Birlikte alınan ürünlerin ne sıklıkla alındığını say.
    product_counts = Counter(item.product_id for item in co_purchased_items)

    # 4. Adım: En sık alınan ürünleri sırala ve ID'lerini döndür.
    recommended_product_ids = [pid for pid, count in product_counts.most_common(limit)]

    return recommended_product_ids