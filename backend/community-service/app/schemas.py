# community-service/app/schemas.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from typing import List

class ReviewBase(BaseModel):
    rating: int = Field(..., gt=0, le=5) # Puan 1-5 arası olmalı
    comment_text: Optional[str] = None

class ReviewCreate(ReviewBase):
    pass

class Review(ReviewBase):
    id: int
    product_id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ForumPostBase(BaseModel):
    post_text: str
    attached_product_link: Optional[str] = None
    attached_image_url: Optional[str] = None

class ForumPostCreate(ForumPostBase):
    pass

class ForumPost(ForumPostBase):
    id: int
    thread_id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ForumThreadBase(BaseModel):
    thread_title: str
    ai_summary: Optional[str] = None
    related_product_id: Optional[int] = None

class ForumThread(ForumThreadBase):
    id: int
    created_at: datetime
    posts: List[ForumPost] = []

    class Config:
        from_attributes = True        