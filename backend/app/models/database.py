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
from sqlalchemy.sql import func
import os

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./thesis_helper.db")

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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


class ThesisProject(Base):
    """Main thesis project table."""
    __tablename__ = "thesis_projects"
    
    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    
    # Thesis details
    thesis_topic = Column(String, nullable=False)
    thesis_description = Column(Text, nullable=False)
    thesis_field = Column(String, nullable=False)
    thesis_deadline = Column(DateTime, nullable=False)
    
    # User preferences
    daily_hours_available = Column(Integer, nullable=False)
    work_days_per_week = Column(Integer, nullable=False)
    focus_duration = Column(Integer, nullable=False)
    procrastination_level = Column(String, nullable=False)
    writing_style = Column(String, nullable=False)
    ai_provider = Column(String, nullable=False, default="ollama")
    
    # Progress tracking
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    completion_percentage = Column(Float, default=0.0)
    
    # Notion integration
    notion_workspace_url = Column(String, nullable=True)
    notion_task_db_id = Column(String, nullable=True)
    notion_milestone_db_id = Column(String, nullable=True)
    notion_main_page_id = Column(String, nullable=True)
    notion_progress_page_id = Column(String, nullable=True)
    
    # Timeline data as JSON
    timeline_data = Column(JSON, nullable=True)
    
    # Relationships
    phases = relationship("ThesisPhase", back_populates="project", cascade="all, delete-orphan")
    milestones = relationship("ThesisMilestone", back_populates="project", cascade="all, delete-orphan")

class ThesisPhase(Base):
    """Thesis phases table."""
    __tablename__ = "thesis_phases"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("thesis_projects.id"), nullable=False)
    
    name = Column(String, nullable=False)
    description = Column(Text)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    estimated_hours = Column(Integer, nullable=False)
    phase_order = Column(Integer, nullable=False)
    
    # Progress
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    actual_hours = Column(Integer, default=0)
    
    # Relationships
    project = relationship("ThesisProject", back_populates="phases")
    tasks = relationship("ThesisTask", back_populates="phase", cascade="all, delete-orphan")

class ThesisTask(Base):
    """Individual tasks table."""
    __tablename__ = "thesis_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    phase_id = Column(Integer, ForeignKey("thesis_phases.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("thesis_projects.id"), nullable=False)
    
    title = Column(String, nullable=False)
    description = Column(Text)
    estimated_hours = Column(Integer, nullable=False)
    priority = Column(Integer, default=1)
    due_date = Column(DateTime, nullable=False)
    
    # Progress
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    actual_hours = Column(Integer, default=0)
    
    # Notion integration
    notion_task_id = Column(String, nullable=True)
    
    # Relationships
    phase = relationship("ThesisPhase", back_populates="tasks")
    project = relationship("ThesisProject")

class ThesisMilestone(Base):
    """Thesis milestones table."""
    __tablename__ = "thesis_milestones"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("thesis_projects.id"), nullable=False)
    
    name = Column(String, nullable=False)
    description = Column(Text)
    target_date = Column(DateTime, nullable=False)
    deliverables = Column(JSON)  # List of deliverables
    
    # Progress
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Notion integration
    notion_milestone_id = Column(String, nullable=True)
    
    # Relationships
    project = relationship("ThesisProject", back_populates="milestones")

# Create all tables
def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)

# Database dependency
def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database
if __name__ == "__main__":
    create_tables()
    print("✅ Database tables created successfully!") 