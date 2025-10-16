from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import os
from cryptography.fernet import Fernet

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    twitter_keys = Column(Text)  # Encrypted JSON: {"api_key": "...", ...}
    preferences = Column(JSON, default={})  # {"prompt": "...", "posting_hours": [9,23], "tone": "critical", "category": "bjp"}
    subscription_tier = Column(String, default="free")  # "free" or "paid"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class NewsPost(Base):
    __tablename__ = "news_posts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    content = Column(Text)
    posted_at = Column(DateTime)
    status = Column(String, default="pending")  # "pending", "posted", "skipped"
    daily_count = Column(Integer, default=0)  # For free tier limits

# Encryption helper (use env var for key in prod)
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key())
cipher_suite = Fernet(ENCRYPTION_KEY)

def encrypt_keys(keys_dict: dict) -> str:
    return cipher_suite.encrypt(json.dumps(keys_dict).encode()).decode()

def decrypt_keys(encrypted: str) -> dict:
    return json.loads(cipher_suite.decrypt(encrypted.encode()).decode())

# DB Setup (SQLite for dev; use postgres:// for prod)
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./baas_bot.db")
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
