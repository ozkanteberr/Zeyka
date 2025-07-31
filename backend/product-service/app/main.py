import numpy as np

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from typing import List
from jose import JWTError

from . import crud, models, schemas, security
from .database import SessionLocal, engine
from fastapi.middleware.cors import CORSMiddleware

from fastapi import File, UploadFile 
from sentence_transformers import SentenceTransformer
from PIL import Image
import requests
from io import BytesIO


models.Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = [
    "http://localhost:3000", # Next.js'in varsayılan adresi
    "http://localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Tüm metodlara izin ver (GET, POST, etc.)
    allow_headers=["*"], # Tüm başlıklara izin ver
)
# Basit bir "Authorization" başlığı bekleyen yeni güvenlik şemamız
API_KEY_SCHEME = APIKeyHeader(name="Authorization", auto_error=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(API_KEY_SCHEME)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token or not token.startswith("Bearer "):
        raise credentials_exception

    # "Bearer " ön ekini kaldır
    token = token.split(" ")[1]

    try:
        payload = security.jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return email


@app.post("/products/", response_model=schemas.Product)
def create_product_endpoint(
    product: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    print(f"Product created by: {current_user}")
    return crud.create_product(db=db, product=product)


@app.get("/products/", response_model=List[schemas.Product])
def read_products_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    products = crud.get_products(db, skip=skip, limit=limit)
    return products
@app.get("/products/{product_id}", response_model=schemas.Product)
def read_product_endpoint(product_id: int, db: Session = Depends(get_db)):
    db_product = crud.get_product(db, product_id=product_id)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

print("AI modeli (CLIP) yükleniyor...")
clip_model = SentenceTransformer('clip-ViT-B-32')
print("AI modeli başarıyla yüklendi.")

@app.get("/search/", response_model=List[schemas.Product])
def search_products_endpoint(q: str, db: Session = Depends(get_db)):
    if not q:
        return []

    print(f"'{q}' için anlamsal arama yapılıyor...")
    query_vector = clip_model.encode(q).tolist() 

    products = crud.search_products_by_vector(db, query_vector=query_vector)
    return products

@app.post("/visual-search/", response_model=List[schemas.Product])
async def visual_search_endpoint(db: Session = Depends(get_db), file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Yüklenen dosya bir resim olmalıdır.")

    try:
        # Yüklenen resmi bellekte aç
        image_bytes = await file.read()
        image = Image.open(BytesIO(image_bytes))

        # Resmi, yapay zeka modeliyle bir vektöre dönüştür
        query_vector = clip_model.encode(image).tolist()

        # Bu vektöre en benzer ürünleri veritabanında ara
        products = crud.search_products_by_image_vector(db, query_vector=query_vector)
        return products
    except Exception as e:
        print(f"Görsel arama sırasında hata: {e}")
        raise HTTPException(status_code=500, detail="Resim işlenirken bir hata oluştu.")
