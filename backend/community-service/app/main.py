# community-service/app/main.py
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from fastapi.middleware.cors import CORSMiddleware


from . import crud, models, schemas, security
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS Ayarları
origins = ["http://localhost:3000"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/products/{product_id}/reviews", response_model=List[schemas.Review])
def read_reviews_for_product(
    product_id: int,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    reviews = crud.get_reviews_for_product(db, product_id=product_id, skip=skip, limit=limit)
    return reviews

# MEVCUT POST ENDPOINT'İ
@app.post("/products/{product_id}/reviews", response_model=schemas.Review)
def create_review_for_product(
    product_id: int,
    review: schemas.ReviewCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(security.get_current_user_id) 
):
    # Yorumu oluştur
    new_review = crud.create_product_review(db=db, review=review, product_id=product_id, user_id=user_id)
    # Yorum oluşturulduktan sonra AI analizini tetikle
    crud.analyze_reviews_and_create_thread(db=db, product_id=product_id)
    return new_review

@app.get("/forums", response_model=List[schemas.ForumThread])
def read_forum_threads(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    threads = crud.get_forum_threads(db, skip=skip, limit=limit)
    return threads

@app.get("/forums/{thread_id}", response_model=schemas.ForumThread)
def read_forum_thread(thread_id: int, db: Session = Depends(get_db)):
    thread = crud.get_forum_thread(db, thread_id=thread_id)
    if thread is None:
        raise HTTPException(status_code=404, detail="Forum thread not found")
    return thread

@app.post("/forums/{thread_id}/posts", response_model=schemas.ForumPost)
def create_post_for_thread(
    thread_id: int,
    post: schemas.ForumPostCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(security.get_current_user_id)
):
    return crud.create_forum_post(db=db, post=post, thread_id=thread_id, user_id=user_id)