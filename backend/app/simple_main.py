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

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

# Import existing modules
from backend.app.core.config import settings
from backend.app.models.schemas import (
    UserQuestionnaireRequest, ThesisField, 
    ProcrastinationLevel, WritingStyle, NotionWorkspaceRequest, NotionSyncRequest
)
from backend.app.services.ai_service import ThesisAIPlannerAgent
from backend.app.services.email_service import EmailService
from backend.app.integrations.notion_client import NotionThesisManager
from backend.app.services.thesis_service import thesis_service
from backend.app.services.task_work_service import TaskWorkService
from backend.app.models.database import get_db
from sqlalchemy.orm import Session


# Pydantic models for brainstorming
class BrainstormingMessage(BaseModel):
    message: str
    conversation_history: List[Dict[str, str]] = []
    user_field: Optional[str] = None
    ai_provider: str = "ollama"

class TopicFinalization(BaseModel):
    conversation_history: List[Dict[str, str]]
    user_field: str
    ai_provider: str = "ollama"

# Pydantic models for task work
class TaskStartRequest(BaseModel):
    task_id: str
    user_id: str
    task_info: Dict[str, Any]

class TaskChatMessage(BaseModel):
    task_id: str
    message: str
    tool_request: Optional[Dict[str, Any]] = None

class TaskToolRequest(BaseModel):
    task_id: str
    tool_name: str
    tool_params: Dict[str, Any]

class TaskCompletionRequest(BaseModel):
    task_id: str
    deliverable: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Simple lifespan manager."""
    global ai_service, email_service, notion_service, task_work_service
    
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
    
    # Initialize Notion service
    try:
        notion_service = NotionThesisManager()
        print("✅ Notion service initialized successfully")
    except Exception as e:
        print(f"❌ Notion service initialization failed: {e}")
        notion_service = None
    
    # Initialize Task Work service
    try:
        task_work_service = TaskWorkService(ai_service)
        print("✅ Task Work service initialized successfully")
    except Exception as e:
        print(f"❌ Task Work service initialization failed: {e}")
        task_work_service = None
    
    print(f"🔍 Service status: AI={ai_service is not None}, Email={email_service is not None}, Notion={notion_service is not None}, TaskWork={task_work_service is not None}")
    
    if ai_service is None and email_service is None and notion_service is None and task_work_service is None:
        print("⚠️ WARNING: No services initialized successfully")
    elif ai_service is None:
        print("⚠️ WARNING: AI service failed to initialize")
    elif email_service is None:
        print("⚠️ WARNING: Email service failed to initialize")
    elif notion_service is None:
        print("⚠️ WARNING: Notion service failed to initialize")
    elif task_work_service is None:
        print("⚠️ WARNING: Task Work service failed to initialize")
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
notion_service = None
task_work_service = None


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
            "notion_service": notion_service is not None,
            "config": settings.APP_NAME == "Thesis Helper"
        }
    }


@app.post("/api/generate-timeline")
async def generate_timeline(user_data: UserQuestionnaireRequest, db: Session = Depends(get_db)):
    """Generate timeline and save to database."""
    try:
        if not ai_service:
            raise HTTPException(status_code=503, detail="AI service not available")
        
        # Generate timeline
        result = ai_service.generate_timeline(user_data, user_data.thesis_description or "")
        
        # Extract the actual timeline data (not the full result with metadata)
        timeline_data = result.get("timeline", {})
        
        # Save to database - pass the timeline data, not the full result
        project = thesis_service.save_thesis_project(user_data, timeline_data, db)
        
        return {
            "success": True,
            "project_id": project.id,
            "message": "Timeline generated and saved successfully",
            "timeline": {
                "timeline": timeline_data,
                "metadata": result.get("metadata", {})
            },
            "user_info": {
                "name": user_data.name,
                "thesis_topic": user_data.thesis_topic,
                "deadline": user_data.thesis_deadline.strftime("%Y-%m-%d")
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
async def create_notion_workspace_endpoint(request: NotionWorkspaceRequest, db: Session = Depends(get_db)):
    """Create Notion workspace and save workspace info to database."""
    try:
        if not notion_service:
            raise HTTPException(status_code=503, detail="Notion service not available")
        
        workspace_info = notion_service.create_student_workspace(
            user_name=request.user_name,
            thesis_topic=request.thesis_topic,
            thesis_description=request.thesis_description
        )
        
        # If project_id is provided, save workspace info to database
        if request.project_id:
            thesis_service.update_notion_workspace_info(
                project_id=request.project_id,
                workspace_url=workspace_info.get("main_page", {}).get("url", ""),
                task_db_id=workspace_info.get("task_database", {}).get("id", ""),
                milestone_db_id=workspace_info.get("milestone_database", {}).get("id", ""),
                main_page_id=workspace_info.get("main_page", {}).get("id", ""),
                progress_page_id=workspace_info.get("progress_page", {}).get("id", ""),
                db=db
            )
        
        return {
            "success": True,
            "message": "Notion workspace created successfully",
            **workspace_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create Notion workspace: {str(e)}")

@app.post("/api/sync-timeline-to-notion")
async def sync_timeline_to_notion_endpoint(
    sync_data: NotionSyncRequest, 
    db: Session = Depends(get_db)
):
    """Sync timeline to Notion and update database."""
    try:
        if not notion_service:
            raise HTTPException(status_code=503, detail="Notion service not available")
        
        # Prepare user_info dict for the notion service
        user_info = {
            "user_name": sync_data.user_name,
            "project_id": sync_data.project_id
        }
        
        result = notion_service.sync_timeline_to_notion(
            timeline_data=sync_data.timeline_data,
            workspace=sync_data.workspace_info,
            user_info=user_info
        )
        
        # If project_id is provided, update workspace info in database
        if hasattr(sync_data, 'project_id') and sync_data.project_id:
            workspace_info = sync_data.workspace_info
            if workspace_info:
                thesis_service.update_notion_workspace_info(
                    project_id=sync_data.project_id,
                    workspace_url=workspace_info.get("main_page", {}).get("url", ""),
                    task_db_id=workspace_info.get("task_database", {}).get("id", ""),
                    milestone_db_id=workspace_info.get("milestone_database", {}).get("id", ""),
                    main_page_id=workspace_info.get("main_page", {}).get("id", ""),
                    progress_page_id=workspace_info.get("progress_page", {}).get("id", ""),
                    db=db
                )
        
        return {
            "success": True,
            "message": "Timeline synced to Notion successfully",
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync timeline to Notion: {str(e)}")


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


@app.post("/api/brainstorm-chat")
async def brainstorm_chat(chat_data: BrainstormingMessage):
    """Interactive brainstorming chat for thesis topic development."""
    try:
        # Create AI service with user's preferred provider
        ai_service = ThesisAIPlannerAgent(ai_provider=chat_data.ai_provider)
        
        # Get brainstorming response
        response = ai_service.brainstorm_thesis_topic(
            message=chat_data.message,
            conversation_history=chat_data.conversation_history,
            user_field=chat_data.user_field
        )
        
        return {
            "success": True,
            "response": response["response"],
            "topic_clarity": response["topic_clarity"],
            "suggested_topic": response.get("suggested_topic"),
            "suggested_description": response.get("suggested_description"),
            "next_question": response.get("next_question")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Brainstorming failed: {str(e)}")


@app.post("/api/finalize-topic")
async def finalize_topic(finalization_data: TopicFinalization):
    """Extract final thesis topic and description from brainstorming conversation."""
    try:
        # Create AI service with user's preferred provider
        ai_service = ThesisAIPlannerAgent(ai_provider=finalization_data.ai_provider)
        
        # Finalize topic from conversation
        result = ai_service.finalize_thesis_topic(
            conversation_history=finalization_data.conversation_history,
            user_field=finalization_data.user_field
        )
        
        return {
            "success": True,
            "thesis_topic": result["thesis_topic"],
            "thesis_description": result["thesis_description"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Topic finalization failed: {str(e)}")


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

@app.get("/api/thesis-projects")
async def get_thesis_projects(db: Session = Depends(get_db)):
    """Get all active thesis projects."""
    try:
        projects = thesis_service.get_active_thesis_projects(db)
        return {
            "success": True,
            "projects": [
                {
                    "id": project.id,
                    "thesis_topic": project.thesis_topic,
                    "thesis_field": project.thesis_field,
                    "user_name": project.user_name,
                    "thesis_deadline": project.thesis_deadline.isoformat(),
                    "created_at": project.created_at.isoformat(),
                    "completion_percentage": project.completion_percentage,
                    "notion_workspace_url": project.notion_workspace_url
                }
                for project in projects
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get thesis projects: {str(e)}")

@app.get("/api/thesis-projects/{project_id}")
async def get_thesis_project(project_id: int, db: Session = Depends(get_db)):
    """Get a specific thesis project by ID."""
    try:
        project = thesis_service.get_thesis_project_by_id(project_id, db)
        if not project:
            raise HTTPException(status_code=404, detail="Thesis project not found")
        
        # Convert to timeline format for frontend
        timeline_data = project.timeline_data or {}
        progress_data = thesis_service.get_project_progress(project_id, db)
        
        return {
            "success": True,
            "project": {
                "id": project.id,
                "user_name": project.user_name,
                "email": project.email,
                "thesis_topic": project.thesis_topic,
                "thesis_description": project.thesis_description,
                "thesis_field": project.thesis_field,
                "thesis_deadline": project.thesis_deadline.isoformat(),
                "daily_hours_available": project.daily_hours_available,
                "work_days_per_week": project.work_days_per_week,
                "focus_duration": project.focus_duration,
                "procrastination_level": project.procrastination_level,
                "writing_style": project.writing_style,
                "ai_provider": project.ai_provider,
                "created_at": project.created_at.isoformat(),
                "notion_workspace_url": project.notion_workspace_url,
                "notion_task_db_id": project.notion_task_db_id,
                "notion_milestone_db_id": project.notion_milestone_db_id,
                "notion_main_page_id": project.notion_main_page_id,
                "notion_progress_page_id": project.notion_progress_page_id,
                "timeline_data": timeline_data,
                "progress": progress_data
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get thesis project: {str(e)}")

@app.get("/api/latest-thesis")
async def get_latest_thesis(db: Session = Depends(get_db)):
    """Get the latest active thesis project."""
    try:
        project = thesis_service.get_latest_thesis_project(db)
        if not project:
            return {"success": True, "project": None}
        
        timeline_data = project.timeline_data or {}
        progress_data = thesis_service.get_project_progress(project.id, db)
        
        return {
            "success": True,
            "project": {
                "id": project.id,
                "user_name": project.user_name,
                "email": project.email,
                "thesis_topic": project.thesis_topic,
                "thesis_description": project.thesis_description,
                "thesis_field": project.thesis_field,
                "thesis_deadline": project.thesis_deadline.isoformat(),
                "daily_hours_available": project.daily_hours_available,
                "work_days_per_week": project.work_days_per_week,
                "focus_duration": project.focus_duration,
                "procrastination_level": project.procrastination_level,
                "writing_style": project.writing_style,
                "ai_provider": project.ai_provider,
                "created_at": project.created_at.isoformat(),
                "notion_workspace_url": project.notion_workspace_url,
                "timeline_data": timeline_data,
                "progress": progress_data
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get latest thesis: {str(e)}")

@app.delete("/api/thesis-projects/{project_id}")
async def deactivate_thesis_project(project_id: int, db: Session = Depends(get_db)):
    """Deactivate (soft delete) a thesis project."""
    try:
        success = thesis_service.deactivate_thesis_project(project_id, db)
        if not success:
            raise HTTPException(status_code=404, detail="Thesis project not found")
        
        return {"success": True, "message": "Thesis project deactivated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to deactivate thesis project: {str(e)}")


# Task Work Endpoints
@app.post("/api/task/start")
async def start_task_session(request: TaskStartRequest):
    """Start a new task work session."""
    if not task_work_service:
        raise HTTPException(status_code=503, detail="Task work service not available")
    
    try:
        result = task_work_service.start_task_session(
            task_id=request.task_id,
            user_id=request.user_id,
            task_info=request.task_info
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to start task session"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start task session: {str(e)}")

@app.post("/api/task/chat")
async def task_chat(request: TaskChatMessage):
    """Process a user message in a task work session."""
    if not task_work_service:
        raise HTTPException(status_code=503, detail="Task work service not available")
    
    try:
        result = task_work_service.process_user_message(
            task_id=request.task_id,
            message=request.message,
            tool_request=request.tool_request
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to process message"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process task message: {str(e)}")

@app.post("/api/task/tool")
async def use_task_tool(request: TaskToolRequest):
    """Use a specific tool in a task work session."""
    if not task_work_service:
        raise HTTPException(status_code=503, detail="Task work service not available")
    
    try:
        result = task_work_service.use_tool(
            task_id=request.task_id,
            tool_name=request.tool_name,
            tool_params=request.tool_params
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to use tool: {str(e)}")

@app.post("/api/task/complete")
async def complete_task(request: TaskCompletionRequest):
    """Complete a task and save the deliverable."""
    if not task_work_service:
        raise HTTPException(status_code=503, detail="Task work service not available")
    
    try:
        result = task_work_service.complete_task(
            task_id=request.task_id,
            deliverable=request.deliverable
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to complete task"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete task: {str(e)}")

@app.get("/api/task/status/{task_id}")
async def get_task_status(task_id: str):
    """Get the status of a task work session."""
    if not task_work_service:
        raise HTTPException(status_code=503, detail="Task work service not available")
    
    try:
        result = task_work_service.get_task_status(task_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Task session not found"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")


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