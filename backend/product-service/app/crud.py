# product-service/app/crud.py
from sqlalchemy.orm import Session
from . import models, schemas
from sqlalchemy.sql import text
from sqlalchemy import or_
from sqlalchemy import cast, Numeric

def get_products(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Product).offset(skip).limit(limit).all()

def create_product(db: Session, product: schemas.ProductCreate):
    db_product = models.Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product
def get_product(db: Session, product_id: int):
    return db.query(models.Product).filter(models.Product.id == product_id).first()

def search_products_by_vector(db: Session, query_vector: list, category: str | None = None, limit: int = 10):
    # Temel sorguyu oluştur
    sql_query = "SELECT * FROM products WHERE embedding IS NOT NULL"
    params = {"query_vector": str(query_vector), "limit": limit}

    # Eğer bir kategori filtresi varsa, sorguya WHERE koşulu olarak ekle
    if category:
        sql_query += " AND category = :category"
        params["category"] = category

    # Sorguyu sıralama ve limit ile tamamla
    sql_query += " ORDER BY embedding <=> :query_vector LIMIT :limit"

    results = db.query(models.Product).from_statement(
        text(sql_query)
    ).params(**params).all()
    return results

def search_products_by_image_vector(db: Session, query_vector: list, limit: int = 10):
    results = db.query(models.Product).from_statement(
        text("SELECT * FROM products WHERE embedding IS NOT NULL ORDER BY embedding <=> :query_vector LIMIT :limit")
    ).params(query_vector=str(query_vector), limit=limit).all()
    return results


def search_products_by_keyword(db: Session, query: str | None = None, category: str | None = None, max_price: float | None = None, limit: int = 100):
    db_query = db.query(models.Product)

    if category:
        db_query = db_query.filter(models.Product.category.ilike(f"%{category}%"))

    if query:
        search_term = f"%{query}%"
        db_query = db_query.filter(or_(
            models.Product.name.ilike(search_term),
            models.Product.description.ilike(search_term)
        ))

    # --- NİHAİ DÜZELTME BURADA ---
    if max_price is not None:
        # Gelen max_price değerini de veritabanında DECIMAL tipine dönüştürerek karşılaştırıyoruz.
        # Bu, tüm olası float/decimal hassasiyet sorunlarını ortadan kaldırır.
        db_query = db_query.filter(models.Product.price <= cast(max_price, Numeric))
    # -----------------------------
    print("--- OLUŞTURULAN SQL SORGUSU ---")
    print(str(db_query.limit(limit).statement.compile(compile_kwargs={"literal_binds": True})))
    print("----------------------------")
    return db_query.limit(limit).all()

def test_price_and_category_filter(db: Session, max_price: float | None = None, category: str | None = None):
    db_query = db.query(models.Product)

    if category:
        db_query = db_query.filter(models.Product.category.ilike(f"%{category}%"))

    if max_price is not None:
        db_query = db_query.filter(cast(models.Product.price, Numeric) <= max_price)

    return db_query.all()