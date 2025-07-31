from sqlalchemy.sql import func
from .database import Base

from sqlalchemy import Column, Integer, String, Text, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship

class ProductReview(Base):
    __tablename__ = "product_reviews"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    rating = Column(Integer, nullable=False)
    comment_text = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class ForumThread(Base):
    __tablename__ = "forum_threads"
    id = Column(Integer, primary_key=True, index=True)
    thread_title = Column(String, nullable=False)
    ai_summary = Column(Text)
    related_product_id = Column(Integer, ForeignKey("products.id")) # products tablosuna referans
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    posts = relationship("ForumPost", back_populates="thread")

class ForumPost(Base):
    __tablename__ = "forum_posts"
    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, ForeignKey("forum_threads.id"))
    user_id = Column(Integer, nullable=False)
    post_text = Column(Text, nullable=False)
    attached_product_link = Column(String)
    attached_image_url = Column(String)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    thread = relationship("ForumThread", back_populates="posts")    