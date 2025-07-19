from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    entries = relationship("CountEntry", back_populates="user")
    article_counts = relationship("UserArticleCount", back_populates="user")

class CountEntry(Base):
    __tablename__ = "count_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    amount = Column(Integer)
    entry_type = Column(String, default="beer")  # beer, birell, entry
    note = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="entries")

class Settings(Base):
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, index=True)
    beer_price = Column(Float, default=50.0)
    birell_price = Column(Float, default=30.0)
    entry_price = Column(Float, default=100.0)
    payment_account = Column(String, default="123456789/0100")
    payment_qr_data = Column(Text, nullable=True)

class Article(Base):
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)  # "Pivo", "Birell", "Vstupné"
    price = Column(Float)
    emoji = Column(String, default="📦")
    payment_account = Column(String, nullable=True)  # Oddělený účet pro tento článek
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class UserArticleCount(Base):
    __tablename__ = "user_article_counts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    article_id = Column(Integer, ForeignKey("articles.id"), index=True)
    count = Column(Integer, default=0)
    
    user = relationship("User", back_populates="article_counts")
    article = relationship("Article")




