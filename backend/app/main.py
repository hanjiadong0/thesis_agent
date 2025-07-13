"""
Main FastAPI application for the Thesis Helper.

This module sets up the FastAPI application with all routes, middleware,
and configuration for the Thesis Helper system.

Author: Thesis Helper Team
Date: 2024
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn
from datetime import datetime

# Import core modules
from backend.app.core.config import settings, get_settings
from backend.app.models.database import create_tables, get_database_engine, get_db
from backend.app.models.schemas import (
    UserQuestionnaireRequest, UserResponse, ApiResponse, HealthCheckResponse,
    DailyProgressRequest, DailyProgressResponse, TimelineResponse,
    EmergencyReplanRequest, EmergencyReplanResponse, ProductivityAnalytics
)

# Import route modules (we'll create these)
from backend.app.routes import questionnaire, timeline, progress, analytics, email


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    
    This function handles application startup and shutdown events.
    It initializes the database and sets up background tasks.
    """
    # Startup
    print("🚀 Starting Thesis Helper application...")
    
    # Initialize database
    engine = get_database_engine(settings.DATABASE_URL)
    create_tables(engine)
    print("✅ Database tables created")
    
    # Start background tasks (email scheduler)
    from backend.app.services.email_scheduler import start_email_scheduler
    start_email_scheduler()
    print("✅ Email scheduler started")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Thesis Helper application...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered thesis planning and progress tracking system",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (for serving React frontend)
app.mount("/static", StaticFiles(directory="frontend/build/static"), name="static")


# Health check endpoint
@app.get("/api/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check endpoint to verify system status.
    
    Returns:
        HealthCheckResponse: System health status
    """
    # Check database connection
    database_connected = True
    try:
        engine = get_database_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            conn.execute("SELECT 1")
    except Exception:
        database_connected = False
    
    # Check AI service
    ai_service_available = True
    try:
        from backend.app.services.ai_service import test_ai_connection
        ai_service_available = test_ai_connection()
    except Exception:
        ai_service_available = False
    
    # Check Notion connection
    notion_connected = True
    try:
        from backend.app.integrations.notion_client import test_notion_connection
        notion_connected = test_notion_connection()
    except Exception:
        notion_connected = False
    
    # Check Google Calendar connection
    google_calendar_connected = True
    try:
        from backend.app.integrations.google_calendar import test_calendar_connection
        google_calendar_connected = test_calendar_connection()
    except Exception:
        google_calendar_connected = False
    
    # Check email service
    email_service_available = True
    try:
        from backend.app.services.email_service import test_email_connection
        email_service_available = test_email_connection()
    except Exception:
        email_service_available = False
    
    return HealthCheckResponse(
        status="healthy" if all([
            database_connected,
            ai_service_available,
            notion_connected,
            google_calendar_connected,
            email_service_available
        ]) else "degraded",
        timestamp=datetime.utcnow(),
        version=settings.APP_VERSION,
        database_connected=database_connected,
        ai_service_available=ai_service_available,
        notion_connected=notion_connected,
        google_calendar_connected=google_calendar_connected,
        email_service_available=email_service_available
    )


# Include route modules
app.include_router(questionnaire.router, prefix="/api/questionnaire", tags=["questionnaire"])
app.include_router(timeline.router, prefix="/api/timeline", tags=["timeline"])
app.include_router(progress.router, prefix="/api/progress", tags=["progress"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(email.router, prefix="/api/email", tags=["email"])


# Root endpoint (serves React app)
@app.get("/")
async def root():
    """
    Root endpoint that serves the React frontend.
    
    Returns:
        HTML: React application
    """
    return {"message": "Thesis Helper API is running! Visit /api/docs for API documentation."}


# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors."""
    return {"error": "Endpoint not found", "status_code": 404}


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors."""
    return {"error": "Internal server error", "status_code": 500}


# Main application entry point
if __name__ == "__main__":
    print("🎓 Starting Thesis Helper Development Server...")
    print(f"📊 Database: {settings.DATABASE_URL}")
    print(f"🤖 AI Provider: {settings.AI_PROVIDER}")
    print(f"✉️  Email: {settings.EMAIL_USER}")
    print(f"🔧 Debug Mode: {settings.DEBUG}")
    
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info"
    ) 