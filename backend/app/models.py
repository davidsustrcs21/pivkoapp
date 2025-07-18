from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
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
    count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    entries = relationship("CountEntry", back_populates="user")

class CountEntry(Base):
    __tablename__ = "count_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Integer, default=1)
    timestamp = Column(DateTime, default=datetime.utcnow)
    note = Column(String, nullable=True)
    
    user = relationship("User", back_populates="entries")