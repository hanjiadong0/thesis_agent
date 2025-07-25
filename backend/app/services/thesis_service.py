"""
Thesis database service for managing thesis projects and progress.
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import logging

from backend.app.models.database import (
    ThesisProject, ThesisPhase, ThesisTask, ThesisMilestone,
    get_db, create_tables
)
from backend.app.models.schemas import UserQuestionnaireRequest, TimelineResponse

logger = logging.getLogger(__name__)

class ThesisService:
    """Service for managing thesis projects in the database."""
    
    def __init__(self):
        """Initialize the service and ensure tables exist."""
        create_tables()
    
    def save_thesis_project(self, 
                           user_data: UserQuestionnaireRequest,
                           timeline_data: TimelineResponse,
                           db: Session) -> ThesisProject:
        """
        Save a new thesis project to the database.
        
        Args:
            user_data: User questionnaire data
            timeline_data: Generated timeline data
            db: Database session
            
        Returns:
            Saved ThesisProject instance
        """
        try:
            # Create main thesis project
            project = ThesisProject(
                user_name=user_data.name,
                email=user_data.email,
                thesis_topic=user_data.thesis_topic,
                thesis_description=user_data.thesis_description or "",
                thesis_field=user_data.thesis_field.value,
                thesis_deadline=user_data.thesis_deadline,
                daily_hours_available=user_data.daily_hours_available,
                work_days_per_week=user_data.work_days_per_week,
                focus_duration=user_data.focus_duration,
                procrastination_level=user_data.procrastination_level.value,
                writing_style=user_data.writing_style.value,
                ai_provider=user_data.ai_provider.value,
                timeline_data=timeline_data.dict() if hasattr(timeline_data, 'dict') else timeline_data
            )
            
            db.add(project)
            db.flush()  # Get the project ID
            
            # Save phases
            for phase_idx, phase_data in enumerate(timeline_data.get("phases", [])):
                phase = ThesisPhase(
                    project_id=project.id,
                    name=phase_data.get("name", ""),
                    description=phase_data.get("description", ""),
                    start_date=self._parse_date(phase_data.get("start_date")),
                    end_date=self._parse_date(phase_data.get("end_date")),
                    estimated_hours=phase_data.get("estimated_hours", 0),
                    phase_order=phase_idx + 1
                )
                db.add(phase)
                db.flush()  # Get the phase ID
                
                # Save tasks for this phase
                for task_data in phase_data.get("tasks", []):
                    task = ThesisTask(
                        phase_id=phase.id,
                        project_id=project.id,
                        title=task_data.get("title", ""),
                        description=task_data.get("description", ""),
                        estimated_hours=task_data.get("estimated_hours", 0),
                        priority=task_data.get("priority", 0),
                        due_date=self._parse_date(task_data.get("due_date"))
                    )
                    db.add(task)
            
            # Save milestones
            for milestone_data in timeline_data.get("milestones", []):
                milestone = ThesisMilestone(
                    project_id=project.id,
                    name=milestone_data.get("name", ""),
                    description=milestone_data.get("description", ""),
                    target_date=self._parse_date(milestone_data.get("target_date")),
                    deliverables=milestone_data.get("deliverables", "")
                )
                db.add(milestone)
            
            db.commit()
            db.refresh(project)
            
            logger.info(f"✅ Saved thesis project: {project.thesis_topic}")
            return project
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error saving thesis project: {str(e)}")
            raise
    
    def get_active_thesis_projects(self, db: Session) -> List[ThesisProject]:
        """
        Get all active thesis projects.
        
        Args:
            db: Database session
            
        Returns:
            List of active thesis projects
        """
        return db.query(ThesisProject).filter(ThesisProject.is_active == True).all()
    
    def get_thesis_project_by_id(self, project_id: int, db: Session) -> Optional[ThesisProject]:
        """
        Get a thesis project by ID.
        
        Args:
            project_id: Project ID
            db: Database session
            
        Returns:
            ThesisProject instance or None
        """
        return db.query(ThesisProject).filter(ThesisProject.id == project_id).first()
    
    def get_latest_thesis_project(self, db: Session) -> Optional[ThesisProject]:
        """
        Get the most recently created active thesis project.
        
        Args:
            db: Database session
            
        Returns:
            Latest ThesisProject instance or None
        """
        return (db.query(ThesisProject)
                .filter(ThesisProject.is_active == True)
                .order_by(ThesisProject.created_at.desc())
                .first())
    
    def deactivate_thesis_project(self, project_id: int, db: Session) -> bool:
        """
        Deactivate a thesis project (soft delete).
        
        Args:
            project_id: Project ID
            db: Database session
            
        Returns:
            True if successful, False otherwise
        """
        try:
            project = self.get_thesis_project_by_id(project_id, db)
            if project:
                project.is_active = False
                project.updated_at = datetime.now()
                db.commit()
                logger.info(f"✅ Deactivated thesis project: {project.thesis_topic}")
                return True
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error deactivating thesis project: {str(e)}")
            return False
    
    def update_notion_workspace_info(self, 
                                   project_id: int,
                                   workspace_url: str,
                                   task_db_id: str,
                                   milestone_db_id: str,
                                   main_page_id: str,
                                   progress_page_id: str,
                                   db: Session) -> bool:
        """
        Update Notion workspace information for a project.
        
        Args:
            project_id: Project ID
            workspace_url: Notion workspace URL
            task_db_id: Task database ID
            milestone_db_id: Milestone database ID
            main_page_id: Main page ID
            progress_page_id: Progress page ID
            db: Database session
            
        Returns:
            True if successful, False otherwise
        """
        try:
            project = self.get_thesis_project_by_id(project_id, db)
            if project:
                project.notion_workspace_url = workspace_url
                project.notion_task_db_id = task_db_id
                project.notion_milestone_db_id = milestone_db_id
                project.notion_main_page_id = main_page_id
                project.notion_progress_page_id = progress_page_id
                project.updated_at = datetime.now()
                db.commit()
                logger.info(f"✅ Updated Notion workspace info for project: {project.thesis_topic}")
                return True
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error updating Notion workspace info: {str(e)}")
            return False
    
    def update_task_completion(self, task_id: int, completed: bool, actual_hours: int, db: Session) -> bool:
        """
        Update task completion status.
        
        Args:
            task_id: Task ID
            completed: Whether task is completed
            actual_hours: Actual hours spent
            db: Database session
            
        Returns:
            True if successful, False otherwise
        """
        try:
            task = db.query(ThesisTask).filter(ThesisTask.id == task_id).first()
            if task:
                task.is_completed = completed
                task.actual_hours = actual_hours
                task.completed_at = datetime.now() if completed else None
                db.commit()
                logger.info(f"✅ Updated task completion: {task.title}")
                return True
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error updating task completion: {str(e)}")
            return False
    
    def get_project_progress(self, project_id: int, db: Session) -> Dict[str, Any]:
        """
        Calculate project progress statistics.
        
        Args:
            project_id: Project ID
            db: Database session
            
        Returns:
            Dictionary with progress statistics
        """
        try:
            project = self.get_thesis_project_by_id(project_id, db)
            if not project:
                return {}
            
            total_tasks = len(project.phases[0].tasks) if project.phases else 0
            completed_tasks = sum(1 for phase in project.phases for task in phase.tasks if task.is_completed)
            
            total_milestones = len(project.milestones)
            completed_milestones = sum(1 for milestone in project.milestones if milestone.is_completed)
            
            total_hours = sum(phase.estimated_hours for phase in project.phases)
            completed_hours = sum(task.actual_hours for phase in project.phases for task in phase.tasks if task.is_completed)
            
            progress_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            return {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "total_milestones": total_milestones,
                "completed_milestones": completed_milestones,
                "total_hours": total_hours,
                "completed_hours": completed_hours,
                "progress_percentage": round(progress_percentage, 1),
                "days_remaining": (project.thesis_deadline - datetime.now()).days if project.thesis_deadline > datetime.now() else 0
            }
        except Exception as e:
            logger.error(f"❌ Error calculating project progress: {str(e)}")
            return {}
    
    def _parse_date(self, date_str: str) -> datetime:
        """
        Parse date string to datetime object.
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            
        Returns:
            datetime object
        """
        try:
            if isinstance(date_str, str):
                return datetime.strptime(date_str, "%Y-%m-%d")
            elif isinstance(date_str, date):
                return datetime.combine(date_str, datetime.min.time())
            elif isinstance(date_str, datetime):
                return date_str
            else:
                # Fallback to current date
                return datetime.now()
        except Exception as e:
            logger.warning(f"⚠️ Error parsing date {date_str}: {str(e)}")
            return datetime.now()

# Global instance
thesis_service = ThesisService() 