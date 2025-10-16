from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from models import User, get_db
from bot_logic import auto_run
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def scheduled_job():
    db = next(get_db())
    try:
        active_users = db.query(User).filter(User.is_active == True).all()
        for user in active_users:
            logger.info(f"Running auto for user {user.id}")
            auto_run(user.id)
    finally:
        db.close()

def init_scheduler():
    scheduler = BackgroundScheduler()
    # Hourly, matching your original (9AM-1AM IST = 3:30-19:30 UTC)
    scheduler.add_job(scheduled_job, 'cron', hour='3-19', minute=30)
    scheduler.start()
    return scheduler
