"""
Configuration module for the Thesis Helper application.

This module manages all application settings, API keys, and environment variables.
It provides a centralized configuration system for the entire application.

Author: Thesis Helper Team
Date: 2024
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """
    Application settings and configuration.
    
    This class handles all configuration values including API keys,
    database settings, and application-specific parameters.
    """
    
    # Application Settings
    APP_NAME: str = "Thesis Helper"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database Settings
    DATABASE_URL: str = "sqlite:///./thesis_helper.db"
    
    # API Keys - These will be loaded from environment variables
    NOTION_TOKEN: str = os.getenv("NOTION_TOKEN", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Google OAuth Settings
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/google/callback"
    
    # Email Settings (Gmail SMTP)
    EMAIL_HOST: str = "smtp.gmail.com"
    EMAIL_PORT: int = 587
    EMAIL_USER: str = os.getenv("EMAIL_USER", "")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")
    EMAIL_USE_TLS: bool = True
    
    # Daily Email Settings
    DAILY_EMAIL_TIME: str = "08:00"  # 8 AM
    DAILY_EMAIL_ENABLED: bool = True
    
    # AI Settings
    AI_PROVIDER: str = "gemini"  # Options: "gemini", "groq", "openai"
    AI_MODEL: str = "gemini-1.5-flash"
    AI_TEMPERATURE: float = 0.7
    AI_MAX_TOKENS: int = 1000
    
    # Thesis Planning Settings
    DEFAULT_BUFFER_TIME: float = 0.15  # 15% buffer time for tasks
    MIN_DAILY_WORK_HOURS: int = 2
    MAX_DAILY_WORK_HOURS: int = 8
    
    # Emergency Replan Settings
    EMERGENCY_THRESHOLD_DAYS: int = 3  # Days behind before emergency replan
    EMERGENCY_COMPLETION_RATE: float = 0.5  # Below 50% completion rate
    
    # Notion Database Settings
    NOTION_DATABASE_NAME: str = "Thesis Tasks"
    NOTION_PAGE_SIZE: int = 100
    
    # Google Calendar Settings
    CALENDAR_NAME: str = "Thesis Helper"
    CALENDAR_TIME_ZONE: str = "UTC"
    
    # Security Settings
    SECRET_KEY: str = "your-secret-key-here"  # Change in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Development Settings
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8000"]
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Get application settings.
    
    Returns:
        Settings: The application settings instance
    """
    return settings


def update_setting(key: str, value: any) -> None:
    """
    Update a setting value at runtime.
    
    Args:
        key: The setting key to update
        value: The new value
    """
    if hasattr(settings, key):
        setattr(settings, key, value)
    else:
        raise ValueError(f"Setting '{key}' does not exist")


def get_database_url() -> str:
    """
    Get the database URL for SQLAlchemy.
    
    Returns:
        str: The database connection URL
    """
    return settings.DATABASE_URL


def get_email_config() -> dict:
    """
    Get email configuration for SMTP.
    
    Returns:
        dict: Email configuration dictionary
    """
    return {
        "host": settings.EMAIL_HOST,
        "port": settings.EMAIL_PORT,
        "username": settings.EMAIL_USER,
        "password": settings.EMAIL_PASSWORD,
        "use_tls": settings.EMAIL_USE_TLS,
    }


def get_ai_config() -> dict:
    """
    Get AI configuration for the planning system.
    
    Returns:
        dict: AI configuration dictionary
    """
    return {
        "provider": settings.AI_PROVIDER,
        "model": settings.AI_MODEL,
        "temperature": settings.AI_TEMPERATURE,
        "max_tokens": settings.AI_MAX_TOKENS,
        "api_key": settings.GEMINI_API_KEY,
    }


def is_development() -> bool:
    """
    Check if the application is running in development mode.
    
    Returns:
        bool: True if in development mode
    """
    return settings.DEBUG 