"""
Pydantic models for API requests and responses.

This module defines all Pydantic models used for API serialization,
validation, and documentation in the Thesis Helper application.

Author: Thesis Helper Team
Date: 2024
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr, validator
from enum import Enum


class ProcrastinationLevel(str, Enum):
    """Enumeration for procrastination levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class WritingStyle(str, Enum):
    """Enumeration for writing styles."""
    DRAFT_THEN_REVISE = "draft_then_revise"
    POLISH_AS_GO = "polish_as_go"


class MotivationLevel(str, Enum):
    """Enumeration for motivation levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class StressLevel(str, Enum):
    """Enumeration for stress levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ThesisField(str, Enum):
    """Enumeration for thesis fields."""
    COMPUTER_SCIENCE = "Computer Science"
    PSYCHOLOGY = "Psychology"
    BIOLOGY = "Biology"
    CHEMISTRY = "Chemistry"
    PHYSICS = "Physics"
    MATHEMATICS = "Mathematics"
    ENGINEERING = "Engineering"
    BUSINESS = "Business"
    LITERATURE = "Literature"
    HISTORY = "History"
    OTHER = "Other"


class AIProvider(str, Enum):
    """Enumeration for AI providers."""
    OLLAMA = "ollama"  # Local Llama via Ollama
    GEMINI = "gemini"  # Google Gemini API


# User-related models
class UserQuestionnaireRequest(BaseModel):
    """
    Request model for user questionnaire submission.
    
    This model validates and serializes the user's answers to the
    initial questionnaire that helps configure the AI planning system.
    """
    
    # Personal Information
    name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    
    # Thesis Information
    thesis_topic: str = Field(..., min_length=10, max_length=500, description="Thesis topic")
    thesis_field: ThesisField = Field(..., description="Field of study")
    thesis_deadline: date = Field(..., description="Thesis submission deadline")
    thesis_description: Optional[str] = Field(None, max_length=2000, description="Detailed thesis description")
    
    # Working Schedule
    daily_hours_available: int = Field(..., ge=1, le=16, description="Hours available per day")
    preferred_start_time: str = Field(..., pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$", description="Preferred start time (HH:MM)")
    preferred_end_time: str = Field(..., pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$", description="Preferred end time (HH:MM)")
    work_days_per_week: int = Field(..., ge=1, le=7, description="Working days per week")
    
    # User Characteristics
    procrastination_level: ProcrastinationLevel = Field(..., description="Self-assessed procrastination level")
    focus_duration: int = Field(..., ge=15, le=240, description="Focused work duration in minutes")
    writing_style: WritingStyle = Field(..., description="Preferred writing approach")
    
    # Preferences
    email_notifications: bool = Field(True, description="Enable email notifications")
    daily_email_time: str = Field("08:00", pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$", description="Daily email time")
    timezone: str = Field("UTC", description="User's timezone")
    ai_provider: AIProvider = Field(AIProvider.OLLAMA, description="Preferred AI provider (Ollama is free and local)")
    
    @validator('thesis_deadline')
    def validate_deadline(cls, v):
        """Validate that the thesis deadline is in the future."""
        if v <= date.today():
            raise ValueError('Thesis deadline must be in the future')
        return v
    
    @validator('preferred_end_time')
    def validate_time_order(cls, v, values):
        """Validate that end time is after start time."""
        if 'preferred_start_time' in values:
            start_time = values['preferred_start_time']
            if v <= start_time:
                raise ValueError('End time must be after start time')
        return v


class UserResponse(BaseModel):
    """
    Response model for user information.
    
    This model is used to return user information in API responses.
    """
    
    id: int
    name: str
    email: str
    thesis_topic: str
    thesis_field: str
    thesis_deadline: date
    daily_hours_available: int
    procrastination_level: str
    focus_duration: int
    writing_style: str
    created_at: datetime
    
    class Config:
        """Pydantic configuration."""
        orm_mode = True


# Timeline-related models
class TaskRequest(BaseModel):
    """
    Request model for creating or updating tasks.
    """
    
    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, max_length=1000, description="Task description")
    estimated_hours: float = Field(..., ge=0.5, le=24, description="Estimated hours to complete")
    priority: int = Field(..., ge=1, le=5, description="Task priority (1-5)")
    due_date: Optional[date] = Field(None, description="Task due date")
    phase: str = Field(..., description="Thesis phase (e.g., literature_review, methodology)")


class TaskResponse(BaseModel):
    """
    Response model for task information.
    """
    
    id: int
    title: str
    description: Optional[str]
    estimated_hours: float
    priority: int
    due_date: Optional[date]
    phase: str
    completed: bool
    completed_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        """Pydantic configuration."""
        orm_mode = True


class MilestoneResponse(BaseModel):
    """
    Response model for milestone information.
    """
    
    id: int
    title: str
    description: Optional[str]
    target_date: date
    completion_percentage: float
    is_completed: bool
    completed_at: Optional[datetime]


class TimelineResponse(BaseModel):
    """
    Response model for timeline information.
    """
    
    id: int
    user_id: int
    current_phase: str
    progress_percentage: float
    original_end_date: date
    current_end_date: date
    days_ahead_behind: int
    milestones: List[MilestoneResponse]
    replan_count: int
    last_replan_date: Optional[date]
    
    class Config:
        """Pydantic configuration."""
        orm_mode = True


# Progress tracking models
class DailyProgressRequest(BaseModel):
    """
    Request model for updating daily progress.
    """
    
    tasks_completed: int = Field(..., ge=0, description="Number of tasks completed")
    hours_worked: float = Field(..., ge=0, le=24, description="Hours worked")
    focus_sessions: int = Field(..., ge=0, description="Number of focus sessions")
    motivation_level: MotivationLevel = Field(..., description="Current motivation level")
    stress_level: StressLevel = Field(..., description="Current stress level")
    user_notes: Optional[str] = Field(None, max_length=1000, description="User notes and reflections")


class DailyProgressResponse(BaseModel):
    """
    Response model for daily progress information.
    """
    
    id: int
    user_id: int
    date: date
    tasks_planned: int
    tasks_completed: int
    completion_rate: float
    hours_worked: float
    hours_planned: float
    focus_sessions: int
    productivity_score: float
    motivation_level: str
    stress_level: str
    user_notes: Optional[str]
    ai_insights: Optional[str]
    
    class Config:
        """Pydantic configuration."""
        orm_mode = True


# Analytics models
class ProductivityAnalytics(BaseModel):
    """
    Response model for productivity analytics.
    """
    
    avg_daily_completion_rate: float
    avg_daily_hours: float
    productivity_trend: str  # "improving", "stable", "declining"
    best_productivity_day: str
    total_tasks_completed: int
    total_hours_worked: float
    streak_days: int
    
    
class WeeklyReport(BaseModel):
    """
    Response model for weekly progress report.
    """
    
    week_start: date
    week_end: date
    total_tasks_planned: int
    total_tasks_completed: int
    total_hours_worked: float
    avg_daily_completion_rate: float
    productivity_score: float
    key_achievements: List[str]
    areas_for_improvement: List[str]


# Email models
class DailyEmailContent(BaseModel):
    """
    Model for daily email content.
    """
    
    subject: str
    greeting: str
    progress_summary: str
    today_tasks: List[str]
    motivational_message: str
    streak_info: str
    overall_status: str


# Emergency replan models
class EmergencyReplanRequest(BaseModel):
    """
    Request model for emergency replan.
    """
    
    reason: str = Field(..., min_length=10, max_length=500, description="Reason for emergency replan")
    new_constraints: Optional[Dict[str, Any]] = Field(None, description="New constraints or limitations")
    priority_adjustments: Optional[Dict[str, int]] = Field(None, description="Priority adjustments for phases")


class EmergencyReplanResponse(BaseModel):
    """
    Response model for emergency replan results.
    """
    
    success: bool
    message: str
    new_timeline: TimelineResponse
    adjustments_made: List[str]
    impact_analysis: Dict[str, Any]


# API response models
class ApiResponse(BaseModel):
    """
    Generic API response model.
    """
    
    success: bool
    message: str
    data: Optional[Any] = None
    errors: Optional[List[str]] = None


class HealthCheckResponse(BaseModel):
    """
    Health check response model.
    """
    
    status: str
    timestamp: datetime
    version: str
    database_connected: bool
    ai_service_available: bool
    notion_connected: bool
    google_calendar_connected: bool
    email_service_available: bool 


class NotionWorkspaceRequest(BaseModel):
    """Request model for creating Notion workspace."""
    user_name: str = Field(..., description="User's name")
    thesis_topic: str = Field(..., description="Thesis topic")
    thesis_description: str = Field(..., description="Thesis description")
    project_id: Optional[int] = Field(None, description="Optional project ID to link workspace")

class ThesisProjectSummary(BaseModel):
    """Summary model for thesis project list."""
    id: int
    thesis_topic: str
    thesis_field: str
    user_name: str
    thesis_deadline: str
    created_at: str
    completion_percentage: float
    notion_workspace_url: Optional[str]

class ThesisProjectResponse(BaseModel):
    """Response model for thesis project details."""
    success: bool
    project: Optional[Dict] = None
    projects: Optional[List[ThesisProjectSummary]] = None
    message: Optional[str] = None 

class NotionSyncRequest(BaseModel):
    """Request model for syncing timeline to Notion."""
    timeline_data: Dict = Field(..., description="Timeline data to sync")
    workspace_info: Dict = Field(..., description="Notion workspace information")
    user_name: str = Field(..., description="User's name")
    project_id: Optional[int] = Field(None, description="Optional project ID to update") 