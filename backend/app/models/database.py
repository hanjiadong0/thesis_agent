"""
Database models for the Thesis Helper application.

This module defines all database models using SQLAlchemy ORM.
It includes models for users, progress tracking, AI patterns, and system events.

Author: Thesis Helper Team
Date: 2024
"""

from datetime import datetime, date
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Date, Float, Boolean, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create the base class for all models
Base = declarative_base()


class User(Base):
    """
    User model for storing user profile and preferences.
    
    This model stores all user-related information including personal details,
    thesis information, and user preferences for the AI planning system.
    """
    
    __tablename__ = "users"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # User identification
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    
    # Thesis information
    thesis_topic = Column(String, nullable=False)
    thesis_field = Column(String, nullable=False)  # e.g., "Computer Science", "Psychology"
    thesis_deadline = Column(Date, nullable=False)
    thesis_description = Column(Text, nullable=True)
    
    # Working preferences
    daily_hours_available = Column(Integer, default=6)  # Hours per day
    preferred_start_time = Column(String, default="09:00")  # HH:MM format
    preferred_end_time = Column(String, default="17:00")  # HH:MM format
    work_days_per_week = Column(Integer, default=5)  # Days per week
    
    # User characteristics (for AI personalization)
    procrastination_level = Column(String, default="medium")  # low, medium, high
    focus_duration = Column(Integer, default=90)  # Minutes of focused work
    writing_style = Column(String, default="draft_then_revise")  # draft_then_revise, polish_as_go
    
    # Preferences
    email_notifications = Column(Boolean, default=True)
    daily_email_time = Column(String, default="08:00")
    timezone = Column(String, default="UTC")
    
    # Notion integration
    notion_database_id = Column(String, nullable=True)
    notion_page_id = Column(String, nullable=True)
    
    # Google Calendar integration
    google_calendar_id = Column(String, nullable=True)
    google_refresh_token = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    progress_records = relationship("DailyProgress", back_populates="user")
    patterns = relationship("UserPattern", back_populates="user")
    events = relationship("SystemEvent", back_populates="user")
    timeline = relationship("ThesisTimeline", back_populates="user", uselist=False)


class DailyProgress(Base):
    """
    Daily progress tracking model.
    
    This model tracks daily completion rates, hours worked, and task progress
    for generating insights and daily email reports.
    """
    
    __tablename__ = "daily_progress"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Date tracking
    date = Column(Date, nullable=False, index=True)
    
    # Task completion
    tasks_planned = Column(Integer, default=0)
    tasks_completed = Column(Integer, default=0)
    completion_rate = Column(Float, default=0.0)  # Percentage (0.0 to 1.0)
    
    # Time tracking
    hours_worked = Column(Float, default=0.0)
    hours_planned = Column(Float, default=0.0)
    
    # Productivity metrics
    focus_sessions = Column(Integer, default=0)
    break_count = Column(Integer, default=0)
    productivity_score = Column(Float, default=0.0)  # 0.0 to 1.0
    
    # Emotional/motivational tracking
    motivation_level = Column(String, default="medium")  # low, medium, high
    stress_level = Column(String, default="medium")  # low, medium, high
    
    # Notes and reflections
    user_notes = Column(Text, nullable=True)
    ai_insights = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="progress_records")


class UserPattern(Base):
    """
    AI-learned patterns about user behavior.
    
    This model stores insights the AI learns about user work patterns,
    preferences, and productivity trends for better timeline adaptation.
    """
    
    __tablename__ = "user_patterns"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Pattern identification
    pattern_type = Column(String, nullable=False)  # e.g., "productivity_time", "task_preference"
    pattern_name = Column(String, nullable=False)  # e.g., "morning_productive", "writing_struggles"
    
    # Pattern data
    pattern_data = Column(JSON, nullable=False)  # Stores complex pattern information
    confidence_score = Column(Float, default=0.0)  # 0.0 to 1.0
    
    # Pattern metadata
    observations_count = Column(Integer, default=1)
    first_observed = Column(Date, default=date.today)
    last_observed = Column(Date, default=date.today)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="patterns")


class SystemEvent(Base):
    """
    System events and logs.
    
    This model tracks important system events like timeline adjustments,
    emergency replans, email sends, and other significant actions.
    """
    
    __tablename__ = "system_events"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Event information
    event_type = Column(String, nullable=False)  # e.g., "timeline_adjustment", "emergency_replan"
    event_category = Column(String, nullable=False)  # e.g., "system", "user_action", "ai_decision"
    
    # Event data
    event_data = Column(JSON, nullable=True)  # Stores event-specific information
    event_message = Column(Text, nullable=True)
    
    # Event status
    status = Column(String, default="completed")  # pending, completed, failed
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="events")


class ThesisTimeline(Base):
    """
    Main thesis timeline and milestone tracking.
    
    This model stores the current thesis timeline, milestones, and
    tracks progress against the planned schedule.
    """
    
    __tablename__ = "thesis_timeline"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timeline information
    timeline_data = Column(JSON, nullable=False)  # Stores the complete timeline
    milestones = Column(JSON, nullable=False)  # Stores milestone information
    
    # Current status
    current_phase = Column(String, nullable=False)  # e.g., "literature_review", "methodology"
    progress_percentage = Column(Float, default=0.0)  # Overall progress (0.0 to 1.0)
    
    # Timeline metadata
    original_end_date = Column(Date, nullable=False)
    current_end_date = Column(Date, nullable=False)
    days_ahead_behind = Column(Integer, default=0)  # Negative if behind, positive if ahead
    
    # Emergency replan tracking
    replan_count = Column(Integer, default=0)
    last_replan_date = Column(Date, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="timeline")


# Database engine and session setup
def get_database_engine(database_url: str):
    """
    Create and return a SQLAlchemy engine.
    
    Args:
        database_url: The database connection URL
        
    Returns:
        SQLAlchemy engine instance
    """
    engine = create_engine(database_url)
    return engine


def get_database_session(engine):
    """
    Create and return a database session.
    
    Args:
        engine: SQLAlchemy engine instance
        
    Returns:
        Database session
    """
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def create_tables(engine):
    """
    Create all database tables.
    
    Args:
        engine: SQLAlchemy engine instance
    """
    Base.metadata.create_all(bind=engine)


def drop_tables(engine):
    """
    Drop all database tables.
    
    Args:
        engine: SQLAlchemy engine instance
    """
    Base.metadata.drop_all(bind=engine)


# Database session dependency for FastAPI
def get_db():
    """
    Database session dependency for FastAPI.
    
    This function provides a database session for each request
    and ensures proper cleanup after the request is complete.
    
    Yields:
        Database session
    """
    from backend.app.core.config import get_database_url
    
    engine = get_database_engine(get_database_url())
    db = get_database_session(engine)
    try:
        yield db
    finally:
        db.close() 