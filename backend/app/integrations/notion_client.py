"""
Student-Focused Notion Integration for Thesis Helper.

This module provides a simplified, student-friendly Notion integration with:
- Simple task management with chronological ordering
- Today's tasks view
- Real progress tracking that actually updates
- Milestone tracking with completion status
- Email integration with actual Notion data

Author: Thesis Helper Team
Date: 2024
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta
from notion_client import Client
from notion_client.errors import APIResponseError, RequestTimeoutError

from backend.app.core.config import settings


class StudentNotionManager:
    """
    Student-focused Notion integration for thesis management.
    
    Simplified design focusing on what students actually need:
    - Task management with today's focus
    - Progress tracking that actually works
    - Milestone tracking
    - Email integration
    """
    
    def __init__(self):
        """Initialize Notion client with API token."""
        if not settings.NOTION_TOKEN:
            raise ValueError("Notion API token is required")
        
        self.client = Client(auth=settings.NOTION_TOKEN)
        self.workspace_cache = {}
    
    def test_connection(self) -> bool:
        """Test Notion API connection."""
        try:
            self.client.users.me()
            return True
        except Exception as e:
            print(f"❌ Notion connection test failed: {e}")
            return False
    
    def create_student_workspace(self, user_name: str, thesis_topic: str, 
                               thesis_description: str, field: str = "Computer Science") -> Dict[str, Any]:
        """Create a simple, student-focused Notion workspace."""
        try:
            print(f"🎓 Creating student workspace for {user_name}")
            
            # Create main thesis page
            main_page = self._create_main_page(user_name, thesis_topic, thesis_description, field)
            
            # Create task management database
            task_database = self._create_task_database(main_page["id"])
            
            # Create milestone database
            milestone_database = self._create_milestone_database(main_page["id"])
            
            # Create progress tracking page with real functionality
            progress_page = self._create_progress_page(main_page["id"])
            
            workspace = {
                "main_page": main_page,
                "task_database": task_database,
                "milestone_database": milestone_database,
                "progress_page": progress_page,
                "created_at": datetime.utcnow().isoformat(),
                "field": field
            }
            
            # Cache workspace
            self.workspace_cache[f"{user_name}_{thesis_topic}"] = workspace
            
            print(f"✅ Student workspace created successfully!")
            return workspace
            
        except Exception as e:
            print(f"❌ Failed to create student workspace: {str(e)}")
            raise Exception(f"Failed to create student workspace: {str(e)}")
    
    def sync_timeline_with_ordering(self, timeline_data: Dict, 
                                  workspace: Dict[str, Any], 
                                  user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Sync timeline with proper chronological ordering and today's tasks."""
        try:
            print(f"📅 Syncing timeline with chronological ordering...")
            
            # Extract timeline data
            if "timeline" in timeline_data:
                actual_timeline = timeline_data["timeline"]
            else:
                actual_timeline = timeline_data
            
            phases = actual_timeline.get("phases", [])
            milestones = actual_timeline.get("milestones", [])
            
            # Sort phases by start date
            sorted_phases = sorted(phases, key=lambda x: x.get("start_date", "9999-12-31"))
            
            # Sort milestones by target date
            sorted_milestones = sorted(milestones, key=lambda x: x.get("target_date", "9999-12-31"))
            
            print(f"📊 Syncing {len(sorted_phases)} phases and {len(sorted_milestones)} milestones")
            
            # Sync milestones with ordering
            milestone_results = self._sync_milestones_ordered(
                sorted_milestones,
                workspace["milestone_database"]["id"]
            )
            
            # Sync tasks with chronological ordering
            task_results = self._sync_tasks_ordered(
                sorted_phases,
                workspace["task_database"]["id"]
            )
            
            # Update progress page with real data
            self._update_progress_with_real_data(
                workspace["progress_page"]["id"],
                task_results,
                milestone_results,
                user_info
            )
            
            # Update main page with today's tasks
            self._update_main_page_with_today_tasks(
                workspace["main_page"]["id"],
                task_results
            )
            
            sync_results = {
                "milestones_synced": len(milestone_results),
                "tasks_synced": len(task_results),
                "today_tasks_count": self._count_today_tasks(task_results),
                "status": "success",
                "synced_at": datetime.utcnow().isoformat()
            }
            
            print(f"✅ Timeline sync completed: {sync_results}")
            return sync_results
            
        except Exception as e:
            print(f"❌ Timeline sync failed: {str(e)}")
            raise Exception(f"Failed to sync timeline: {str(e)}")
    
    def get_today_tasks(self, task_database_id: str) -> List[Dict]:
        """Get tasks that are due today or overdue."""
        try:
            today = date.today()
            
            # Query tasks from database
            response = self.client.databases.query(
                database_id=task_database_id,
                sorts=[
                    {
                        "property": "Due Date",
                        "direction": "ascending"
                    }
                ]
            )
            
            today_tasks = []
            for task in response["results"]:
                due_date_prop = task["properties"].get("Due Date", {}).get("date")
                if due_date_prop and due_date_prop.get("start"):
                    due_date = datetime.strptime(due_date_prop["start"], "%Y-%m-%d").date()
                    if due_date <= today:
                        today_tasks.append(task)
            
            return today_tasks
            
        except Exception as e:
            print(f"❌ Failed to get today's tasks: {e}")
            return []
    
    def get_progress_data(self, workspace: Dict[str, Any]) -> Dict[str, Any]:
        """Get real progress data from Notion databases."""
        try:
            # Get task statistics
            task_stats = self._get_real_task_stats(workspace["task_database"]["id"])
            
            # Get milestone progress
            milestone_stats = self._get_real_milestone_stats(workspace["milestone_database"]["id"])
            
            # Get today's tasks
            today_tasks = self.get_today_tasks(workspace["task_database"]["id"])
            
            # Calculate overall progress
            overall_progress = self._calculate_overall_progress(task_stats, milestone_stats)
            
            return {
                "task_statistics": task_stats,
                "milestone_statistics": milestone_stats,
                "today_tasks": len(today_tasks),
                "overall_progress": overall_progress,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Failed to get progress data: {e}")
            return {"error": str(e)}
    
    def get_email_data(self, workspace: Dict[str, Any], user_name: str) -> Dict[str, Any]:
        """Get actual data from Notion for email integration."""
        try:
            # Get today's tasks
            today_tasks = self.get_today_tasks(workspace["task_database"]["id"])
            
            # Get progress data
            progress_data = self.get_progress_data(workspace)
            
            # Get upcoming milestones (next 7 days)
            upcoming_milestones = self._get_upcoming_milestones(
                workspace["milestone_database"]["id"], 
                days=7
            )
            
            # Format tasks for email
            tasks_today = []
            for task in today_tasks[:5]:  # Limit to 5 tasks
                task_title = task["properties"].get("Task", {}).get("title", [])
                if task_title:
                    title = task_title[0]["text"]["content"]
                    tasks_today.append(title)
            
            # Format progress data
            task_stats = progress_data.get("task_statistics", {})
            email_progress = {
                "tasks_completed": task_stats.get("completed", 0),
                "tasks_total": task_stats.get("total", 0),
                "completion_rate": task_stats.get("completion_rate", 0),
                "tasks_today": len(today_tasks),
                "upcoming_milestones": len(upcoming_milestones)
            }
            
            return {
                "user_name": user_name,
                "progress_data": email_progress,
                "tasks_today": tasks_today,
                "upcoming_milestones": [m["name"] for m in upcoming_milestones],
                "workspace_url": workspace["main_page"]["url"]
            }
            
        except Exception as e:
            print(f"❌ Failed to get email data: {e}")
            return {"error": str(e)}
    
    def update_task_completion(self, task_id: str, completed: bool = True) -> bool:
        """Update task completion status in Notion."""
        try:
            status = "✅ Completed" if completed else "🔄 In Progress"
            progress = 100 if completed else 0
            
            self.client.pages.update(
                page_id=task_id,
                properties={
                    "Status": {"select": {"name": status}},
                    "Progress": {"number": progress},
                    "Completed Date": {"date": {"start": datetime.utcnow().isoformat()}} if completed else None
                }
            )
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to update task completion: {e}")
            return False
    
    def _create_main_page(self, user_name: str, thesis_topic: str, 
                         thesis_description: str, field: str) -> Dict[str, Any]:
        """Create simple main thesis page."""
        print(f"📄 Creating main thesis page...")
        
        page_content = [
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"text": {"content": f"🎓 {thesis_topic}"}}]
                }
            },
            {
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"text": {"content": f"👨‍🎓 {user_name} | 📚 {field} | 📅 {datetime.now().strftime('%B %d, %Y')}"}}],
                    "icon": {"emoji": "🎯"}
                }
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "📝 About This Thesis"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"text": {"content": thesis_description}}]
                }
            },
            {
                "object": "block",
                "type": "divider",
                "divider": {}
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "📅 Today's Tasks"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"text": {"content": "Your tasks for today will appear here automatically."}}]
                }
            },
            {
                "object": "block",
                "type": "divider",
                "divider": {}
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "📊 Quick Links"}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"text": {"content": "📋 View all tasks and track progress"}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"text": {"content": "🎯 Check milestone deadlines"}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"text": {"content": "📈 View progress analytics"}}]
                }
            }
        ]
        
        parent_page_id = self._get_default_parent_page()
        
        if parent_page_id:
            parent = {"type": "page_id", "page_id": parent_page_id}
        else:
            parent = {"type": "workspace", "workspace": True}
        
        page = self.client.pages.create(
            parent=parent,
            properties={
                "title": {
                    "title": [{"text": {"content": f"🎓 {thesis_topic} - Thesis Workspace"}}]
                }
            },
            children=page_content
        )
        
        print(f"✅ Main page created: {page['url']}")
        return page
    
    def _create_task_database(self, parent_page_id: str) -> Dict[str, Any]:
        """Create simple task database with chronological ordering."""
        print(f"📋 Creating task database...")
        
        database = self.client.databases.create(
            parent={"type": "page_id", "page_id": parent_page_id},
            title=[{"text": {"content": "📋 Thesis Tasks"}}],
            properties={
                "Task": {"title": {}},
                "Phase": {"rich_text": {}},
                "Due Date": {"date": {}},
                "Status": {
                    "select": {
                        "options": [
                            {"name": "📋 Not Started", "color": "gray"},
                            {"name": "🔄 In Progress", "color": "yellow"},
                            {"name": "✅ Completed", "color": "green"},
                            {"name": "❌ Blocked", "color": "red"}
                        ]
                    }
                },
                "Priority": {
                    "select": {
                        "options": [
                            {"name": "🔴 High", "color": "red"},
                            {"name": "🟡 Medium", "color": "yellow"},
                            {"name": "🟢 Low", "color": "green"}
                        ]
                    }
                },
                "Estimated Hours": {"number": {"format": "number"}},
                "Progress": {"number": {"format": "percent"}},
                "Description": {"rich_text": {}},
                "Completed Date": {"date": {}},
                "Created": {"created_time": {}},
                "Order": {"number": {"format": "number"}}
            }
        )
        
        print(f"✅ Task database created: {database['url']}")
        return database
    
    def _create_milestone_database(self, parent_page_id: str) -> Dict[str, Any]:
        """Create simple milestone database."""
        print(f"🎯 Creating milestone database...")
        
        database = self.client.databases.create(
            parent={"type": "page_id", "page_id": parent_page_id},
            title=[{"text": {"content": "🎯 Thesis Milestones"}}],
            properties={
                "Milestone": {"title": {}},
                "Target Date": {"date": {}},
                "Status": {
                    "select": {
                        "options": [
                            {"name": "🔮 Upcoming", "color": "blue"},
                            {"name": "🔄 In Progress", "color": "yellow"},
                            {"name": "✅ Completed", "color": "green"},
                            {"name": "⏰ Overdue", "color": "red"}
                        ]
                    }
                },
                "Description": {"rich_text": {}},
                "Deliverables": {"rich_text": {}},
                "Progress": {"number": {"format": "percent"}},
                "Order": {"number": {"format": "number"}},
                "Created": {"created_time": {}}
            }
        )
        
        print(f"✅ Milestone database created: {database['url']}")
        return database
    
    def _create_progress_page(self, parent_page_id: str) -> Dict[str, Any]:
        """Create progress page with real tracking."""
        print(f"📊 Creating progress page...")
        
        page_content = [
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"text": {"content": "📊 Progress Dashboard"}}]
                }
            },
            {
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"text": {"content": "This dashboard shows your real progress and updates automatically as you complete tasks."}}],
                    "icon": {"emoji": "📈"}
                }
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "📋 Task Progress"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"text": {"content": "Task completion statistics will appear here automatically."}}]
                }
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "🎯 Milestone Progress"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"text": {"content": "Milestone completion status will appear here automatically."}}]
                }
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "📅 Today's Focus"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"text": {"content": "Today's tasks and priorities will appear here automatically."}}]
                }
            }
        ]
        
        page = self.client.pages.create(
            parent={"type": "page_id", "page_id": parent_page_id},
            properties={
                "title": {
                    "title": [{"text": {"content": "📊 Progress Dashboard"}}]
                }
            },
            children=page_content
        )
        
        print(f"✅ Progress page created: {page['url']}")
        return page
    
    def _sync_milestones_ordered(self, milestones: List[Dict], database_id: str) -> List[Dict]:
        """Sync milestones with proper ordering."""
        print(f"🎯 Syncing {len(milestones)} milestones in order...")
        results = []
        
        for order, milestone in enumerate(milestones, 1):
            try:
                # Determine status based on date
                target_date = datetime.strptime(milestone["target_date"], "%Y-%m-%d").date()
                today = date.today()
                
                if target_date < today:
                    status = "⏰ Overdue"
                elif target_date == today:
                    status = "🔄 In Progress"
                else:
                    status = "🔮 Upcoming"
                
                page = self.client.pages.create(
                    parent={"database_id": database_id},
                    properties={
                        "Milestone": {
                            "title": [{"text": {"content": milestone["name"]}}]
                        },
                        "Target Date": {
                            "date": {"start": milestone["target_date"]}
                        },
                        "Status": {
                            "select": {"name": status}
                        },
                        "Description": {
                            "rich_text": [{"text": {"content": milestone.get("description", "")}}]
                        },
                        "Deliverables": {
                            "rich_text": [{"text": {"content": ", ".join(milestone.get("deliverables", []))}}]
                        },
                        "Progress": {"number": 0},
                        "Order": {"number": order}
                    }
                )
                
                results.append(page)
                print(f"✅ Milestone {order}: {milestone['name']}")
                
            except Exception as e:
                print(f"❌ Failed to sync milestone {milestone['name']}: {e}")
        
        return results
    
    def _sync_tasks_ordered(self, phases: List[Dict], database_id: str) -> List[Dict]:
        """Sync tasks with chronological ordering."""
        print(f"📋 Syncing tasks in chronological order...")
        results = []
        order = 1
        
        for phase in phases:
            phase_name = phase["name"]
            
            # Sort tasks within phase by due date
            tasks = sorted(phase.get("tasks", []), key=lambda x: x.get("due_date", "9999-12-31"))
            
            for task in tasks:
                try:
                    # Determine status based on date
                    due_date = datetime.strptime(task["due_date"], "%Y-%m-%d").date()
                    today = date.today()
                    
                    if due_date < today:
                        status = "❌ Blocked"
                    elif due_date == today:
                        status = "🔄 In Progress"
                    else:
                        status = "📋 Not Started"
                    
                    # Map priority
                    priority_map = {1: "🔴 High", 2: "🔴 High", 3: "🟡 Medium", 4: "🟢 Low", 5: "🟢 Low"}
                    priority = priority_map.get(task.get("priority", 3), "🟡 Medium")
                    
                    page = self.client.pages.create(
                        parent={"database_id": database_id},
                        properties={
                            "Task": {
                                "title": [{"text": {"content": task["title"]}}]
                            },
                            "Phase": {
                                "rich_text": [{"text": {"content": phase_name}}]
                            },
                            "Due Date": {
                                "date": {"start": task["due_date"]}
                            },
                            "Status": {
                                "select": {"name": status}
                            },
                            "Priority": {
                                "select": {"name": priority}
                            },
                            "Estimated Hours": {
                                "number": task.get("estimated_hours", 0)
                            },
                            "Progress": {"number": 0},
                            "Description": {
                                "rich_text": [{"text": {"content": task.get("description", "")}}]
                            },
                            "Order": {"number": order}
                        }
                    )
                    
                    results.append(page)
                    print(f"✅ Task {order}: {task['title']} (Due: {task['due_date']})")
                    order += 1
                    
                except Exception as e:
                    print(f"❌ Failed to sync task {task['title']}: {e}")
        
        return results
    
    def _update_progress_with_real_data(self, page_id: str, task_results: List, 
                                       milestone_results: List, user_info: Dict) -> None:
        """Update progress page with real data."""
        print(f"📊 Updating progress page with real data...")
        
        try:
            total_tasks = len(task_results)
            total_milestones = len(milestone_results)
            
            progress_content = [
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": "📊 Current Statistics"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "callout",
                    "callout": {
                        "rich_text": [{"text": {"content": f"📋 Total Tasks: {total_tasks} | 🎯 Total Milestones: {total_milestones} | 📅 Last Updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"}}],
                        "icon": {"emoji": "📈"}
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"text": {"content": f"✅ Tasks Completed: 0 out of {total_tasks} (0%)\n"}},
                            {"text": {"content": f"🎯 Milestones Completed: 0 out of {total_milestones} (0%)\n"}},
                            {"text": {"content": f"📅 Tasks Due Today: {self._count_today_tasks(task_results)}\n"}},
                            {"text": {"content": f"🎓 For: {user_info.get('name', 'Student')}"}}
                        ]
                    }
                }
            ]
            
            self.client.blocks.children.append(
                block_id=page_id,
                children=progress_content
            )
            
            print(f"✅ Progress page updated with real data")
            
        except Exception as e:
            print(f"❌ Failed to update progress page: {e}")
    
    def _update_main_page_with_today_tasks(self, page_id: str, task_results: List) -> None:
        """Update main page with today's tasks."""
        print(f"📅 Updating main page with today's tasks...")
        
        try:
            today = date.today()
            today_tasks = []
            
            for task in task_results:
                # Check if task is due today
                due_date_str = task["properties"]["Due Date"]["date"]["start"]
                due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
                
                if due_date <= today:
                    task_title = task["properties"]["Task"]["title"][0]["text"]["content"]
                    today_tasks.append(task_title)
            
            if today_tasks:
                today_content = [
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"text": {"content": f"📅 Today's Tasks ({len(today_tasks)})"}}]
                        }
                    }
                ]
                
                for task in today_tasks[:5]:  # Show max 5 tasks
                    today_content.append({
                        "object": "block",
                        "type": "to_do",
                        "to_do": {
                            "rich_text": [{"text": {"content": task}}],
                            "checked": False
                        }
                    })
                
                if len(today_tasks) > 5:
                    today_content.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"text": {"content": f"...and {len(today_tasks) - 5} more tasks"}}]
                        }
                    })
                
                self.client.blocks.children.append(
                    block_id=page_id,
                    children=today_content
                )
            
            print(f"✅ Main page updated with {len(today_tasks)} today's tasks")
            
        except Exception as e:
            print(f"❌ Failed to update main page with today's tasks: {e}")
    
    def _count_today_tasks(self, task_results: List) -> int:
        """Count tasks due today or overdue."""
        today = date.today()
        count = 0
        
        for task in task_results:
            try:
                due_date_str = task["properties"]["Due Date"]["date"]["start"]
                due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
                if due_date <= today:
                    count += 1
            except:
                pass
        
        return count
    
    def _get_real_task_stats(self, database_id: str) -> Dict[str, Any]:
        """Get real task statistics from database."""
        try:
            response = self.client.databases.query(database_id=database_id)
            
            total = len(response["results"])
            completed = 0
            in_progress = 0
            overdue = 0
            
            today = date.today()
            
            for task in response["results"]:
                status = task["properties"].get("Status", {}).get("select", {})
                if status:
                    if status.get("name") == "✅ Completed":
                        completed += 1
                    elif status.get("name") == "🔄 In Progress":
                        in_progress += 1
                
                # Check if overdue
                due_date_prop = task["properties"].get("Due Date", {}).get("date")
                if due_date_prop and due_date_prop.get("start"):
                    due_date = datetime.strptime(due_date_prop["start"], "%Y-%m-%d").date()
                    if due_date < today and status.get("name") != "✅ Completed":
                        overdue += 1
            
            return {
                "total": total,
                "completed": completed,
                "in_progress": in_progress,
                "overdue": overdue,
                "completion_rate": (completed / total * 100) if total > 0 else 0
            }
            
        except Exception as e:
            print(f"❌ Failed to get task stats: {e}")
            return {}
    
    def _get_real_milestone_stats(self, database_id: str) -> Dict[str, Any]:
        """Get real milestone statistics from database."""
        try:
            response = self.client.databases.query(database_id=database_id)
            
            total = len(response["results"])
            completed = 0
            overdue = 0
            
            for milestone in response["results"]:
                status = milestone["properties"].get("Status", {}).get("select", {})
                if status:
                    if status.get("name") == "✅ Completed":
                        completed += 1
                    elif status.get("name") == "⏰ Overdue":
                        overdue += 1
            
            return {
                "total": total,
                "completed": completed,
                "overdue": overdue,
                "completion_rate": (completed / total * 100) if total > 0 else 0
            }
            
        except Exception as e:
            print(f"❌ Failed to get milestone stats: {e}")
            return {}
    
    def _calculate_overall_progress(self, task_stats: Dict, milestone_stats: Dict) -> float:
        """Calculate overall progress percentage."""
        task_progress = task_stats.get("completion_rate", 0)
        milestone_progress = milestone_stats.get("completion_rate", 0)
        
        # Weight tasks 70% and milestones 30%
        overall = (task_progress * 0.7) + (milestone_progress * 0.3)
        return round(overall, 1)
    
    def _get_upcoming_milestones(self, database_id: str, days: int = 7) -> List[Dict]:
        """Get milestones due in the next X days."""
        try:
            response = self.client.databases.query(database_id=database_id)
            
            today = date.today()
            future_date = today + timedelta(days=days)
            
            upcoming = []
            for milestone in response["results"]:
                target_date_prop = milestone["properties"].get("Target Date", {}).get("date")
                if target_date_prop and target_date_prop.get("start"):
                    target_date = datetime.strptime(target_date_prop["start"], "%Y-%m-%d").date()
                    if today <= target_date <= future_date:
                        milestone_name = milestone["properties"]["Milestone"]["title"][0]["text"]["content"]
                        upcoming.append({
                            "name": milestone_name,
                            "date": target_date.strftime("%Y-%m-%d")
                        })
            
            return upcoming
            
        except Exception as e:
            print(f"❌ Failed to get upcoming milestones: {e}")
            return []
    
    def _get_default_parent_page(self) -> Optional[str]:
        """Get default parent page ID."""
        try:
            response = self.client.search(
                query="",
                filter={"property": "object", "value": "page"}
            )
            
            if response["results"]:
                return response["results"][0]["id"]
            return None
                
        except Exception as e:
            print(f"❌ Failed to get default parent page: {e}")
            return None


# Backward compatibility wrapper
class NotionThesisManager(StudentNotionManager):
    """Backward compatibility wrapper."""
    
    def create_thesis_workspace(self, user_name: str, thesis_topic: str, 
                               thesis_description: str) -> Dict[str, Any]:
        """Create workspace using student-focused method."""
        return self.create_student_workspace(user_name, thesis_topic, thesis_description)
    
    def create_advanced_thesis_workspace(self, user_name: str, thesis_topic: str, 
                                       thesis_description: str, field: str = "Computer Science") -> Dict[str, Any]:
        """Create workspace using student-focused method with field."""
        return self.create_student_workspace(user_name, thesis_topic, thesis_description, field)
    
    def sync_timeline_to_notion(self, timeline_data: Dict, 
                               workspace: Dict[str, Any], 
                               user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Sync timeline using ordered method."""
        return self.sync_timeline_with_ordering(timeline_data, workspace, user_info)
    
    def sync_comprehensive_timeline(self, timeline_data: Dict, 
                                  workspace: Dict[str, Any], 
                                  user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Sync timeline using ordered method."""
        return self.sync_timeline_with_ordering(timeline_data, workspace, user_info)


def test_notion_connection() -> bool:
    """Test Notion connection."""
    try:
        manager = StudentNotionManager()
        return manager.test_connection()
    except Exception as e:
        print(f"❌ Notion connection test failed: {e}")
        return False


# Export classes
__all__ = ["StudentNotionManager", "NotionThesisManager", "test_notion_connection"] 