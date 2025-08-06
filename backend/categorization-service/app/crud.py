# product-service/app/crud.py
from sqlalchemy.orm import Session
from . import models, schemas
from sqlalchemy.sql import text

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

def search_products_by_vector(db: Session, query_vector: list, limit: int = 10):
    results = db.query(models.Product).from_statement(
        text("SELECT * FROM products WHERE embedding IS NOT NULL ORDER BY embedding <=> :query_vector LIMIT :limit")
    ).params(query_vector=str(query_vector), limit=limit).all()
    return results

def search_products_by_image_vector(db: Session, query_vector: list, limit: int = 10):
    results = db.query(models.Product).from_statement(
        text("SELECT * FROM products WHERE embedding IS NOT NULL ORDER BY embedding <=> :query_vector LIMIT :limit")
    ).params(query_vector=str(query_vector), limit=limit).all()
    return results

