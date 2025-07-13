#!/usr/bin/env python3
"""
Simplified FastAPI application for testing the Thesis Helper core functionality.

This version only uses the existing components and doesn't try to import
non-existent modules.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from datetime import datetime, date
from typing import Dict, Any

# Import existing modules
from backend.app.core.config import settings
from backend.app.models.schemas import (
    UserQuestionnaireRequest, ThesisField, 
    ProcrastinationLevel, WritingStyle
)
from backend.app.services.ai_service import ThesisAIPlannerAgent
from backend.app.services.email_service import EmailService
from backend.app.integrations.notion_client import NotionThesisManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Simple lifespan manager."""
    global ai_service, email_service
    
    print("🚀 Starting simplified Thesis Helper...")
    print("🚀 Initializing services...")
    
    # Initialize AI service
    try:
        ai_service = ThesisAIPlannerAgent()
        print("✅ AI service initialized successfully")
    except Exception as e:
        print(f"❌ AI service initialization failed: {e}")
        ai_service = None
    
    # Initialize email service
    try:
        email_service = EmailService()
        print("✅ Email service initialized successfully")
    except Exception as e:
        print(f"❌ Email service initialization failed: {e}")
        email_service = None
    
    print(f"🔍 Service status: AI={ai_service is not None}, Email={email_service is not None}")
    
    if ai_service is None and email_service is None:
        print("⚠️ WARNING: No services initialized successfully")
    elif ai_service is None:
        print("⚠️ WARNING: AI service failed to initialize")
    elif email_service is None:
        print("⚠️ WARNING: Email service failed to initialize")
    else:
        print("✅ All services initialized successfully")
    
    yield
    
    print("🛑 Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Thesis Helper - Simple",
    version="1.0.0",
    description="Simplified version for testing core functionality",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global services
ai_service = None
email_service = None


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Thesis Helper Simple API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "generate_timeline": "/api/generate-timeline",
            "test_email": "/api/test-email"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "ai_service": ai_service is not None,
            "email_service": email_service is not None,
            "config": settings.APP_NAME == "Thesis Helper"
        }
    }


@app.post("/api/generate-timeline")
async def generate_timeline(user_data: UserQuestionnaireRequest):
    """Generate AI timeline for user."""
    if not ai_service:
        raise HTTPException(status_code=503, detail="AI service not available")
    
    try:
        # Generate timeline
        timeline = ai_service.generate_timeline(
            user_data=user_data,
            thesis_description=user_data.thesis_description or "No detailed description provided"
        )
        
        return {
            "success": True,
            "timeline": timeline,
            "user_info": {
                "name": user_data.name,
                "thesis_topic": user_data.thesis_topic,
                "deadline": user_data.thesis_deadline.isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Timeline generation failed: {str(e)}")


@app.post("/api/test-email")
async def test_email(email_data: dict):
    """Test email functionality with actual Notion data."""
    if not email_service:
        raise HTTPException(status_code=503, detail="Email service not available")
    
    try:
        recipient = email_data.get("email", "mouazan99@gmail.com")
        workspace_info = email_data.get("workspace_info")
        user_name = email_data.get("user_name", "Test User")
        
        # Use actual Notion data if workspace is provided
        if workspace_info:
            notion_manager = NotionThesisManager()
            email_notion_data = notion_manager.get_email_data(workspace_info, user_name)
            
            if "error" not in email_notion_data:
                # Use real Notion data
                success = email_service.send_daily_progress_email(
                    user_email=recipient,
                    user_name=email_notion_data["user_name"],
                    progress_data=email_notion_data["progress_data"],
                    tasks_today=email_notion_data["tasks_today"]
                )
                
                return {
                    "success": success,
                    "message": "Email sent with real Notion data!" if success else "Failed to send email with Notion data",
                    "recipient": recipient,
                    "data_source": "notion",
                    "tasks_today": len(email_notion_data["tasks_today"]),
                    "workspace_url": email_notion_data.get("workspace_url")
                }
        
        # Fallback to test data if no workspace provided
        progress_data = {
            "tasks_completed": 4,
            "tasks_total": 10,
            "completion_rate": 40.0,
            "tasks_today": 3,
            "upcoming_milestones": 2
        }
        
        tasks_today = [
            "Review research papers on climate ML",
            "Implement data preprocessing pipeline", 
            "Write methodology section"
        ]
        
        success = email_service.send_daily_progress_email(
            user_email=recipient,
            user_name=user_name,
            progress_data=progress_data,
            tasks_today=tasks_today
        )
        
        return {
            "success": success,
            "message": "Test email sent successfully" if success else "Failed to send test email",
            "recipient": recipient,
            "data_source": "test"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email test failed: {str(e)}")


@app.post("/api/create-notion-workspace")
async def create_notion_workspace(user_data: UserQuestionnaireRequest):
    """Create advanced Notion workspace for thesis management."""
    try:
        notion_manager = NotionThesisManager()
        
        workspace = notion_manager.create_advanced_thesis_workspace(
            user_name=user_data.name,
            thesis_topic=user_data.thesis_topic,
            thesis_description=user_data.thesis_description or "No description provided",
            field=user_data.thesis_field.value if hasattr(user_data.thesis_field, 'value') else user_data.thesis_field
        )
        
        return {
            "success": True,
            "workspace": workspace,
            "message": "Advanced Notion workspace created successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create advanced Notion workspace: {str(e)}")


@app.post("/api/sync-timeline-to-notion")
async def sync_timeline_to_notion(request_data: dict):
    """Sync timeline data to existing Notion workspace with comprehensive features."""
    try:
        timeline_data = request_data.get("timeline_data")
        workspace_info = request_data.get("workspace_info") 
        user_info = request_data.get("user_info")
        
        if not all([timeline_data, workspace_info, user_info]):
            raise HTTPException(status_code=400, detail="Missing required data")
        
        notion_manager = NotionThesisManager()
        
        sync_result = notion_manager.sync_comprehensive_timeline(
            timeline_data=timeline_data,
            workspace=workspace_info,
            user_info=user_info
        )
        
        return {
            "success": True,
            "sync_result": sync_result,
            "message": "Timeline synced to Notion with comprehensive features"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync comprehensive timeline to Notion: {str(e)}")


@app.get("/api/notion-workspace-summary/{workspace_id}")
async def get_notion_workspace_summary(workspace_id: str):
    """Get summary of Notion workspace."""
    try:
        notion_manager = NotionThesisManager()
        
        # For now, return cached workspace info
        # In production, you'd fetch from database based on workspace_id
        
        return {
            "success": True,
            "summary": {
                "workspace_id": workspace_id,
                "status": "active",
                "last_updated": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workspace summary: {str(e)}")


@app.post("/api/test-notion-connection")
async def test_notion_connection_endpoint():
    """Test Notion API connection."""
    try:
        notion_manager = NotionThesisManager()
        connection_status = notion_manager.test_connection()
        
        return {
            "success": connection_status,
            "message": "Notion connection successful" if connection_status else "Notion connection failed",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Notion connection test failed: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }


@app.get("/api/sample-user")
async def get_sample_user():
    """Get sample user data for testing."""
    return {
        "name": "Alex Johnson",
        "email": "alex.johnson@university.edu",
        "thesis_topic": "Machine Learning Applications in Climate Change Prediction",
        "thesis_field": "COMPUTER_SCIENCE",
        "thesis_deadline": "2025-12-31",
        "thesis_description": "Developing ML models to predict climate patterns using satellite data",
        "daily_hours_available": 7,
        "preferred_start_time": "09:00",
        "preferred_end_time": "18:00",
        "work_days_per_week": 5,
        "procrastination_level": "MEDIUM",
        "focus_duration": 120,
        "writing_style": "DRAFT_THEN_REVISE",
        "email_notifications": True,
        "daily_email_time": "08:00",
        "timezone": "UTC"
    }


if __name__ == "__main__":
    print("🎓 Starting Thesis Helper Simple Server...")
    print(f"📊 Visit: http://localhost:8000")
    print(f"📚 API Docs: http://localhost:8000/docs")
    print(f"🔧 Debug Mode: {settings.DEBUG}")
    
    uvicorn.run(
        "backend.app.simple_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 