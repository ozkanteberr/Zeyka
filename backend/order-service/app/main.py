from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from typing import List
from jose import JWTError

from . import crud, models, schemas, security
from .database import SessionLocal, engine
from fastapi.middleware.cors import CORSMiddleware

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

API_KEY_SCHEME = APIKeyHeader(name="Authorization", auto_error=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user_id(token: str = Depends(API_KEY_SCHEME)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token or not token.startswith("Bearer "):
        raise credentials_exception
    token = token.split(" ")[1]
    try:
        payload = security.jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        # Not: user_id'yi token'a eklemediğimiz için, şimdilik user_id'yi
        # email'den varsayımsal olarak üretiyoruz (örneğin 1).
        # Gerçek uygulamada user_id token'ın içinde olur.
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        return 1 # Varsayımsal Kullanıcı ID'si
    except JWTError:
        raise credentials_exception

@app.post("/orders/", response_model=schemas.Order)
def create_order_endpoint(
    order: schemas.OrderCreate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    return crud.create_order(db=db, order=order, user_id=current_user_id)