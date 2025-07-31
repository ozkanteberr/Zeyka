# community-service/app/crud.py
from sqlalchemy.orm import Session
from . import models, schemas


def create_product_review(db: Session, review: schemas.ReviewCreate, product_id: int, user_id: int):
    db_review = models.ProductReview(
        **review.model_dump(), 
        product_id=product_id, 
        user_id=user_id
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review

def get_reviews_for_product(db: Session, product_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.ProductReview).filter(models.ProductReview.product_id == product_id).offset(skip).limit(limit).all()

def get_forum_threads(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.ForumThread).offset(skip).limit(limit).all()

def get_forum_thread(db: Session, thread_id: int):
    return db.query(models.ForumThread).filter(models.ForumThread.id == thread_id).first()

def create_forum_post(db: Session, post: schemas.ForumPostCreate, thread_id: int, user_id: int):
    db_post = models.ForumPost(
        **post.model_dump(),
        thread_id=thread_id,
        user_id=user_id
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

# AI analiz ve başlık oluşturma fonksiyonunu şimdilik sahte (mock) olarak ekliyoruz
def analyze_reviews_and_create_thread(db: Session, product_id: int):
    reviews = get_reviews_for_product(db, product_id=product_id)
    if len(reviews) < 5: # Örnek olarak, 5 yoruma ulaşınca başlık oluştursun
        return None

    # Gerçek bir uygulamada burada Gemini'ye istek atılır.
    # Şimdilik, son yorumdan bir başlık ve özet üretiyoruz.
    last_review = reviews[-1]
    thread_title = f"ID'si {product_id} olan ürün hakkında yeni tartışma"
    ai_summary = f"Kullanıcılar bu ürün hakkında konuşuyor. Son yorumda '{last_review.comment_text}' denildi. Siz ne düşünüyorsunuz?"

    # Aynı başlığın tekrar oluşmasını engelle
    existing_thread = db.query(models.ForumThread).filter(models.ForumThread.thread_title == thread_title).first()
    if existing_thread:
        return existing_thread

    db_thread = models.ForumThread(
        thread_title=thread_title,
        ai_summary=ai_summary,
        related_product_id=product_id
    )
    db.add(db_thread)
    db.commit()
    db.refresh(db_thread)
    return db_thread