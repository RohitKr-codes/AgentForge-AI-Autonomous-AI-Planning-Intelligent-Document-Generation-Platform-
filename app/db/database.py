"""
database.py
Sets up a local SQLite database using SQLAlchemy. No external DB needed —
the file `data.db` is created automatically in the project root.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

DATABASE_URL = f"sqlite:///{settings.DB_PATH}"

# check_same_thread=False is required for SQLite when used with FastAPI's
# threaded request handling.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and closes it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables if they don't already exist."""
    from app.db import models  # noqa: F401  (ensures models are registered)
    Base.metadata.create_all(bind=engine)
