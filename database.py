# Run this script once: python database.py
from models import Base, engine
Base.metadata.create_all(bind=engine)
print("DB tables created!")
