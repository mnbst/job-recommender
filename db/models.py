"""Database models for job recommender."""

import os
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class User(Base):
    """User model storing GitHub profile and preferences."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    github_username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255))
    profile_data = Column(JSON)  # Generated profile from LLM
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SearchHistory(Base):
    """History of job searches and recommendations."""

    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    query = Column(String(1000))
    results = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


def get_engine():
    """Create database engine from environment."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        # Fallback to SQLite for local development
        database_url = "sqlite:///./job_recommender.db"
    return create_engine(database_url)


def get_session():
    """Get database session."""
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


def init_db():
    """Initialize database tables."""
    engine = get_engine()
    Base.metadata.create_all(engine)
