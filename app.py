from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any
import os
from models import User, NewsPost, get_db, encrypt_keys
from bot_logic import fetch_news, post_next, auto_run
from scheduler import init_scheduler

app = FastAPI(title="BaaS Bot Platform")

# Global scheduler (start on app init)
scheduler = init_scheduler()

class UserCreate(BaseModel):
    username: str
    twitter_keys: Dict[str, str]
    preferences: Dict[str, Any] = {}
    subscription_tier: str = "free"

class SettingsUpdate(BaseModel):
    preferences: Dict[str, Any]

@app.post("/users/")
def create_user(user: UserCreate, db=Depends(get_db)):
    # Check if user exists
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="User exists")
    encrypted_keys = encrypt_keys(user.twitter_keys)
    db_user = User(
        username=user.username,
        twitter_keys=encrypted_keys,
        preferences=user.preferences,
        subscription_tier=user.subscription_tier
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"user_id": db_user.id, "status": "created"}

@app.post("/start_bot/{user_id}")
def start_bot(user_id: int, background_tasks: BackgroundTasks, db=Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=404, detail="User not found or inactive")
    user.is_active = True
    db.commit()
    background_tasks.add_task(auto_run, user_id)  # Trigger once
    return {"status": "Bot started", "user_id": user_id}

@app.post("/stop_bot/{user_id}")
def stop_bot(user_id: int, db=Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    db.commit()
    return {"status": "Bot stopped", "user_id": user_id}

@app.post("/manual_fetch/{user_id}")
def manual_fetch(user_id: int, background_tasks: BackgroundTasks, db=Depends(get_db)):
    news = fetch_news(user_id, db)
    if news:
        clean = clean_news(news)  # From bot_logic
        save_news(user_id, clean, db)
    post_next(user_id, db)
    return {"status": "Fetched and posted", "news": news}

@app.post("/update_settings/{user_id}")
def update_settings(user_id: int, settings: SettingsUpdate, db=Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.preferences.update(settings.preferences)
    db.commit()
    return {"status": "Settings updated", "user_id": user_id}

@app.get("/history/{user_id}")
def get_history(user_id: int, db=Depends(get_db)):
    posts = db.query(NewsPost).filter(NewsPost.user_id == user_id).order_by(NewsPost.posted_at.desc()).limit(50).all()
    return [{"id": p.id, "content": p.content[:100] + "...", "posted_at": p.posted_at, "status": p.status} for p in posts]

# Health check
@app.get("/")
def root():
    return {"message": "BaaS Bot Platform is running!"}
