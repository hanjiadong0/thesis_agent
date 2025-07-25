"""
AI Service for timeline generation and planning.

This module handles AI-powered thesis timeline generation, task breakdown,
and intelligent planning using both Gemini and local Llama models via Ollama.

Author: Thesis Helper Team
Date: 2024
"""

import json
import re
import requests
import google.generativeai as genai
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from abc import ABC, abstractmethod
import re # Added for regex in topic extraction

from backend.app.core.config import settings
from backend.app.models.schemas import UserQuestionnaireRequest, ThesisField


class BaseAIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    def generate_content(self, prompt: str) -> str:
        """Generate content using the AI provider."""
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test connection to the AI provider."""
        pass


class GeminiProvider(BaseAIProvider):
    """Gemini AI provider implementation."""
    
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
    
    def generate_content(self, prompt: str) -> str:
        """Generate content using Gemini."""
        response = self.model.generate_content(prompt)
        return response.text
    
    def test_connection(self) -> bool:
        """Test Gemini connection."""
        try:
            response = self.model.generate_content("Hello")
            return True
        except Exception:
            return False


class OllamaProvider(BaseAIProvider):
    """Ollama (local Llama) AI provider implementation."""
    
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
    
    def generate_content(self, prompt: str) -> str:
        """Generate content using Ollama."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": settings.AI_TEMPERATURE,
                "num_predict": settings.AI_MAX_TOKENS
            }
        }
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=120
        )
        
        if response.status_code == 200:
            return response.json()["response"]
        else:
            raise Exception(f"Ollama request failed: {response.status_code}")
    
    def test_connection(self) -> bool:
        """Test Ollama connection."""
        try:
            # Check if Ollama is running and model is available
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return any(model["name"].startswith(self.model) for model in models)
            return False
        except Exception:
            return False


class AIProviderFactory:
    """Factory class to create AI providers."""
    
    @staticmethod
    def create_provider(provider_type: str) -> BaseAIProvider:
        """Create an AI provider based on type."""
        if provider_type.lower() == "gemini":
            return GeminiProvider()
        elif provider_type.lower() == "ollama":
            return OllamaProvider()
        else:
            raise ValueError(f"Unsupported AI provider: {provider_type}")


class ThesisAIPlannerAgent:
    """
    AI agent for thesis planning and timeline generation.
    
    This class uses either Gemini AI or local Llama models via Ollama to generate 
    personalized thesis timelines based on user preferences, thesis requirements, 
    and productivity patterns.
    """
    
    def __init__(self, ai_provider: str = None):
        """Initialize the AI service with the specified provider."""
        # Use provided provider or default from settings
        self.provider_type = ai_provider or settings.AI_PROVIDER
        self.provider = AIProviderFactory.create_provider(self.provider_type)
        
        # Field-specific knowledge base
        self.field_knowledge = {
            "Computer Science": {
                "typical_phases": [
                    "Literature Review", "Problem Definition", "Methodology Design",
                    "Implementation", "Testing & Validation", "Results Analysis", 
                    "Writing & Documentation", "Revision & Finalization"
                ],
                "phase_weights": {
                    "Literature Review": 0.20,
                    "Problem Definition": 0.08,
                    "Methodology Design": 0.12,
                    "Implementation": 0.25,
                    "Testing & Validation": 0.15,
                    "Results Analysis": 0.10,
                    "Writing & Documentation": 0.15,
                    "Revision & Finalization": 0.05
                },
                "typical_duration_months": 6,
                "implementation_heavy": True
            },
            "Psychology": {
                "typical_phases": [
                    "Literature Review", "Hypothesis Formation", "Study Design",
                    "Data Collection", "Statistical Analysis", "Results Interpretation",
                    "Writing & Documentation", "Revision & Finalization"
                ],
                "phase_weights": {
                    "Literature Review": 0.25,
                    "Hypothesis Formation": 0.08,
                    "Study Design": 0.12,
                    "Data Collection": 0.20,
                    "Statistical Analysis": 0.15,
                    "Results Interpretation": 0.10,
                    "Writing & Documentation": 0.15,
                    "Revision & Finalization": 0.05
                },
                "typical_duration_months": 8,
                "data_collection_heavy": True
            },
            # Add more fields as needed
        }
    
    def generate_timeline(self, user_data: UserQuestionnaireRequest, thesis_description: str) -> Dict[str, Any]:
        """
        Generate a personalized thesis timeline with daily task assignments.
        
        Args:
            user_data: User questionnaire responses
            thesis_description: Detailed thesis description
            
        Returns:
            Dict containing the complete timeline with daily assigned tasks
        """
        # Calculate realistic working parameters
        today = date.today()
        deadline = user_data.thesis_deadline
        total_days = (deadline - today).days
        
        if total_days <= 0:
            raise Exception("Deadline must be in the future")
            
        # Calculate working days more realistically
        working_days_per_week = user_data.work_days_per_week
        total_weeks = total_days // 7
        working_days = (total_weeks * working_days_per_week) + min(total_days % 7, working_days_per_week)
        
        # Realistic time allocation (not all hours are productive)
        daily_productive_hours = user_data.daily_hours_available * 0.8  # 80% efficiency
        total_productive_hours = working_days * daily_productive_hours
        
        # Get field-specific knowledge
        field_info = self.field_knowledge.get(user_data.thesis_field.value, 
                                             self.field_knowledge["Computer Science"])
        
        # Generate timeline using improved AI prompt
        timeline_prompt = self._create_detailed_timeline_prompt(
            user_data, thesis_description, field_info, 
            total_productive_hours, working_days, today, deadline
        )
        
        try:
            response_text = self.provider.generate_content(timeline_prompt)
            timeline_data = self._parse_timeline_response(response_text)
            
            # Assign tasks to specific working days
            timeline_data = self._assign_tasks_to_days(timeline_data, user_data, today, deadline)
            
            return {
                "timeline": timeline_data,
                "metadata": {
                    "total_days": total_days,
                    "working_days": working_days,
                    "total_hours": int(total_productive_hours),
                    "daily_hours": daily_productive_hours,
                    "field": user_data.thesis_field.value,
                    "generated_at": datetime.utcnow().isoformat(),
                    "start_date": today.isoformat(),
                    "deadline": deadline.isoformat(),
                    "ai_provider": self.provider_type
                }
            }
        except Exception as e:
            # Create a more detailed fallback timeline
            timeline_data = self._create_detailed_fallback_timeline(user_data, today, deadline)
            return {
                "timeline": timeline_data,
                "metadata": {
                    "total_days": total_days,
                    "working_days": working_days,
                    "total_hours": int(total_productive_hours),
                    "field": user_data.thesis_field.value,
                    "generated_at": datetime.utcnow().isoformat(),
                    "fallback": True,
                    "error": str(e)
                }
            }

    def _create_detailed_timeline_prompt(self, user_data: UserQuestionnaireRequest, 
                                       thesis_description: str, field_info: Dict, 
                                       total_hours: float, working_days: int,
                                       start_date: date, deadline: date) -> str:
        """Create a detailed prompt for granular timeline generation."""
        
        # Calculate phase distribution
        phase_count = len(field_info["typical_phases"])
        hours_per_phase = total_hours / phase_count
        
        prompt = f"""
        Create a detailed thesis timeline with granular daily tasks.

        STUDENT PROFILE:
        - Field: {user_data.thesis_field.value}
        - Topic: {user_data.thesis_topic}
        - Start Date: {start_date}
        - Deadline: {deadline}
        - Working Days: {working_days}
        - Total Productive Hours: {total_hours:.1f}
        - Daily Hours: {user_data.daily_hours_available}
        - Focus Duration: {user_data.focus_duration} minutes
        - Work Days/Week: {user_data.work_days_per_week}
        - Procrastination Level: {user_data.procrastination_level.value}

        THESIS DESCRIPTION: {thesis_description[:400]}...

        REQUIREMENTS:
        1. Create {phase_count} phases (~{hours_per_phase:.0f}h each)
        2. Break each phase into SMALL, actionable tasks (2-8 hours each)
        3. Each task should fit {user_data.focus_duration}-minute work sessions
        4. ALL dates must be between {start_date} and {deadline}
        5. Create 15-25 total tasks (not just 4!)
        6. Tasks should be specific and actionable

        RESPOND WITH VALID JSON:
        {{
            "phases": [
                {{
                    "name": "Phase Name",
                    "description": "What this phase accomplishes",
                    "start_date": "YYYY-MM-DD",
                    "end_date": "YYYY-MM-DD",
                    "estimated_hours": 80,
                    "tasks": [
                        {{
                            "title": "Specific 2-8 hour task",
                            "description": "Clear actionable description",
                            "estimated_hours": 4,
                            "priority": 1,
                            "due_date": "YYYY-MM-DD",
                            "focus_sessions": 2,
                            "deliverable": "What gets produced"
                        }}
                    ]
                }}
            ],
            "milestones": [
                {{
                    "name": "Major milestone",
                    "description": "Key deliverable",
                    "target_date": "YYYY-MM-DD",
                    "deliverables": ["specific item"]
                }}
            ]
        }}

        Make tasks GRANULAR and ACTIONABLE. Examples:
        - "Read 5 papers on topic X" (4h)
        - "Write introduction section draft" (6h)
        - "Set up experiment environment" (3h)
        - "Code data preprocessing module" (5h)
        """
        
        return prompt

    def _assign_tasks_to_days(self, timeline_data: Dict[str, Any], 
                             user_data: UserQuestionnaireRequest,
                             start_date: date, deadline: date) -> Dict[str, Any]:
        """Assign tasks to specific working days."""
        
        if not isinstance(timeline_data, dict) or "phases" not in timeline_data:
            return timeline_data
            
        # Generate working days between start and deadline
        working_days = self._generate_working_days(start_date, deadline, user_data.work_days_per_week)
        
        # Collect all tasks with their due dates
        all_tasks = []
        for phase in timeline_data.get("phases", []):
            for task in phase.get("tasks", []):
                all_tasks.append(task)
        
        # Sort tasks by due date and priority
        all_tasks.sort(key=lambda t: (t.get("due_date", "9999-12-31"), -t.get("priority", 0)))
        
        # Assign tasks to working days
        day_assignments = {}
        current_day_idx = 0
        daily_hour_capacity = user_data.daily_hours_available
        current_day_hours = 0
        
        for task in all_tasks:
            task_hours = task.get("estimated_hours", 2)
            
            # Find next available day with capacity
            while current_day_idx < len(working_days):
                current_day = working_days[current_day_idx]
                
                if current_day_hours + task_hours <= daily_hour_capacity:
                    # Assign task to this day
                    if current_day not in day_assignments:
                        day_assignments[current_day] = []
                    
                    task["assigned_date"] = current_day.isoformat()
                    day_assignments[current_day].append(task)
                    current_day_hours += task_hours
                    break
                else:
                    # Move to next working day
                    current_day_idx += 1
                    current_day_hours = 0
            
            if current_day_idx >= len(working_days):
                # If we run out of days, assign to last working day
                last_day = working_days[-1]
                task["assigned_date"] = last_day.isoformat()
                if last_day not in day_assignments:
                    day_assignments[last_day] = []
                day_assignments[last_day].append(task)
        
        # Add daily assignments to timeline
        timeline_data["daily_assignments"] = {
            day.isoformat(): tasks for day, tasks in day_assignments.items()
        }
        
        # Add today's tasks if today is a working day
        today = date.today()
        timeline_data["todays_tasks"] = day_assignments.get(today, [])
        
        return timeline_data

    def _generate_working_days(self, start_date: date, end_date: date, work_days_per_week: int) -> List[date]:
        """Generate list of working days between start and end date."""
        working_days = []
        current = start_date
        
        # Define which days of week are working days (0=Monday, 6=Sunday)
        # Assume work days are Monday through Friday, adjust based on work_days_per_week
        if work_days_per_week <= 5:
            work_weekdays = list(range(work_days_per_week))  # 0-4 for Mon-Fri
        else:
            work_weekdays = list(range(6))  # Mon-Sat for 6+ days
            
        while current <= end_date:
            if current.weekday() in work_weekdays:
                working_days.append(current)
            current += timedelta(days=1)
            
        return working_days

    def _create_detailed_fallback_timeline(self, user_data: UserQuestionnaireRequest, 
                                         start_date: date, deadline: date) -> Dict[str, Any]:
        """Create a detailed fallback timeline with granular tasks."""
        print("🔄 Creating detailed fallback timeline with task assignments")
        
        total_days = (deadline - start_date).days
        phase_duration = total_days // 4  # 4 phases
        
        phases = []
        current_date = start_date
        
        # Phase 1: Literature Review (25% of time)
        phase1_end = current_date + timedelta(days=phase_duration)
        phases.append({
            "name": "Literature Review & Background Research",
            "description": "Comprehensive review of existing research and background study",
            "start_date": current_date.isoformat(),
            "end_date": phase1_end.isoformat(),
            "estimated_hours": 60,
            "tasks": [
                {
                    "title": "Search and collect relevant academic papers",
                    "description": "Use academic databases to find 20-30 relevant papers",
                    "estimated_hours": 8,
                    "priority": 1,
                    "due_date": (current_date + timedelta(days=5)).isoformat(),
                    "focus_sessions": 4,
                    "deliverable": "Bibliography of 20-30 papers"
                },
                {
                    "title": "Read and summarize key papers (Batch 1)",
                    "description": "Read 10 most relevant papers and create summaries",
                    "estimated_hours": 12,
                    "priority": 1,
                    "due_date": (current_date + timedelta(days=10)).isoformat(),
                    "focus_sessions": 6,
                    "deliverable": "10 paper summaries"
                },
                {
                    "title": "Read and summarize key papers (Batch 2)",
                    "description": "Read remaining 10-15 papers and create summaries",
                    "estimated_hours": 12,
                    "priority": 1,
                    "due_date": (current_date + timedelta(days=15)).isoformat(),
                    "focus_sessions": 6,
                    "deliverable": "Complete literature summary"
                },
                {
                    "title": "Identify research gaps and opportunities",
                    "description": "Analyze literature to find gaps your research will address",
                    "estimated_hours": 6,
                    "priority": 2,
                    "due_date": (current_date + timedelta(days=18)).isoformat(),
                    "focus_sessions": 3,
                    "deliverable": "Gap analysis document"
                },
                {
                    "title": "Write literature review chapter draft",
                    "description": "Synthesize research into coherent literature review",
                    "estimated_hours": 16,
                    "priority": 1,
                    "due_date": phase1_end.isoformat(),
                    "focus_sessions": 8,
                    "deliverable": "Literature review draft (3000-5000 words)"
                }
            ]
        })
        
        # Phase 2: Methodology & Planning (20% of time)
        current_date = phase1_end + timedelta(days=1)
        phase2_end = current_date + timedelta(days=phase_duration)
        phases.append({
            "name": "Methodology Design & Planning",
            "description": "Design research methodology and create detailed project plan",
            "start_date": current_date.isoformat(),
            "end_date": phase2_end.isoformat(),
            "estimated_hours": 50,
            "tasks": [
                {
                    "title": "Define research questions and hypotheses",
                    "description": "Clearly articulate what your research aims to discover",
                    "estimated_hours": 4,
                    "priority": 1,
                    "due_date": (current_date + timedelta(days=3)).isoformat(),
                    "focus_sessions": 2,
                    "deliverable": "Research questions document"
                },
                {
                    "title": "Design research methodology",
                    "description": "Choose and justify your research approach and methods",
                    "estimated_hours": 8,
                    "priority": 1,
                    "due_date": (current_date + timedelta(days=7)).isoformat(),
                    "focus_sessions": 4,
                    "deliverable": "Methodology design document"
                },
                {
                    "title": "Create detailed project timeline",
                    "description": "Break down remaining work into specific tasks and deadlines",
                    "estimated_hours": 4,
                    "priority": 2,
                    "due_date": (current_date + timedelta(days=10)).isoformat(),
                    "focus_sessions": 2,
                    "deliverable": "Detailed project plan"
                },
                {
                    "title": "Set up tools and environment",
                    "description": "Install software, set up workspace, prepare tools needed",
                    "estimated_hours": 6,
                    "priority": 1,
                    "due_date": (current_date + timedelta(days=14)).isoformat(),
                    "focus_sessions": 3,
                    "deliverable": "Ready development/research environment"
                },
                {
                    "title": "Write methodology chapter draft",
                    "description": "Document your chosen methodology and justify approach",
                    "estimated_hours": 12,
                    "priority": 1,
                    "due_date": phase2_end.isoformat(),
                    "focus_sessions": 6,
                    "deliverable": "Methodology chapter draft (2000-3000 words)"
                }
            ]
        })
        
        # Phase 3: Implementation & Data Collection (35% of time)  
        current_date = phase2_end + timedelta(days=1)
        phase3_end = current_date + timedelta(days=int(phase_duration * 1.4))
        phases.append({
            "name": "Implementation & Data Collection",
            "description": "Execute research plan, build solutions, collect and analyze data",
            "start_date": current_date.isoformat(),
            "end_date": phase3_end.isoformat(),
            "estimated_hours": 90,
            "tasks": [
                {
                    "title": "Build core system/prototype (Phase 1)",
                    "description": "Implement the main components of your solution",
                    "estimated_hours": 16,
                    "priority": 1,
                    "due_date": (current_date + timedelta(days=8)).isoformat(),
                    "focus_sessions": 8,
                    "deliverable": "Working prototype v1"
                },
                {
                    "title": "Collect initial dataset/conduct initial experiments",
                    "description": "Gather data or run initial tests for your research",
                    "estimated_hours": 12,
                    "priority": 1,
                    "due_date": (current_date + timedelta(days=14)).isoformat(),
                    "focus_sessions": 6,
                    "deliverable": "Initial dataset/experiment results"
                },
                {
                    "title": "Refine and improve implementation",
                    "description": "Iterate on your solution based on initial results",
                    "estimated_hours": 14,
                    "priority": 1,
                    "due_date": (current_date + timedelta(days=21)).isoformat(),
                    "focus_sessions": 7,
                    "deliverable": "Improved prototype v2"
                },
                {
                    "title": "Conduct comprehensive testing/data collection",
                    "description": "Run full experiments or collect complete dataset",
                    "estimated_hours": 16,
                    "priority": 1,
                    "due_date": (current_date + timedelta(days=28)).isoformat(),
                    "focus_sessions": 8,
                    "deliverable": "Complete experimental data"
                },
                {
                    "title": "Analyze results and identify patterns",
                    "description": "Process data and extract meaningful insights",
                    "estimated_hours": 12,
                    "priority": 1,
                    "due_date": phase3_end.isoformat(),
                    "focus_sessions": 6,
                    "deliverable": "Analysis results and findings"
                }
            ]
        })
        
        # Phase 4: Writing & Finalization (20% of time)
        current_date = phase3_end + timedelta(days=1)
        phase4_end = deadline
        phases.append({
            "name": "Writing & Finalization",
            "description": "Write thesis document, revise, and prepare final submission",
            "start_date": current_date.isoformat(),
            "end_date": phase4_end.isoformat(),
            "estimated_hours": 70,
            "tasks": [
                {
                    "title": "Write results chapter",
                    "description": "Document your findings and experimental results",
                    "estimated_hours": 14,
                    "priority": 1,
                    "due_date": (current_date + timedelta(days=7)).isoformat(),
                    "focus_sessions": 7,
                    "deliverable": "Results chapter draft (3000-4000 words)"
                },
                {
                    "title": "Write discussion and analysis chapter",
                    "description": "Interpret results and discuss implications",
                    "estimated_hours": 12,
                    "priority": 1,
                    "due_date": (current_date + timedelta(days=12)).isoformat(),
                    "focus_sessions": 6,
                    "deliverable": "Discussion chapter draft (2500-3500 words)"
                },
                {
                    "title": "Write introduction and conclusion",
                    "description": "Create compelling introduction and strong conclusion",
                    "estimated_hours": 8,
                    "priority": 1,
                    "due_date": (current_date + timedelta(days=16)).isoformat(),
                    "focus_sessions": 4,
                    "deliverable": "Introduction and conclusion drafts"
                },
                {
                    "title": "Integrate all chapters and format thesis",
                    "description": "Combine chapters, format document, add references",
                    "estimated_hours": 8,
                    "priority": 1,
                    "due_date": (current_date + timedelta(days=19)).isoformat(),
                    "focus_sessions": 4,
                    "deliverable": "Complete first draft"
                },
                {
                    "title": "Review, revise and proofread",
                    "description": "Multiple rounds of revision and proofreading",
                    "estimated_hours": 12,
                    "priority": 1,
                    "due_date": (deadline - timedelta(days=2)).isoformat(),
                    "focus_sessions": 6,
                    "deliverable": "Polished final draft"
                },
                {
                    "title": "Final preparation and submission",
                    "description": "Final checks, printing, and submission preparation",
                    "estimated_hours": 4,
                    "priority": 1,
                    "due_date": deadline.isoformat(),
                    "focus_sessions": 2,
                    "deliverable": "Submitted thesis"
                }
            ]
        })
        
        # Create milestones
        milestones = [
            {
                "name": "Literature Review Complete",
                "description": "Comprehensive literature review finished",
                "target_date": phases[0]["end_date"],
                "deliverables": ["Literature review chapter", "Research gap analysis"]
            },
            {
                "name": "Methodology Finalized",
                "description": "Research approach and methodology confirmed",
                "target_date": phases[1]["end_date"],
                "deliverables": ["Methodology chapter", "Project plan", "Setup complete"]
            },
            {
                "name": "Implementation Complete",
                "description": "All development and data collection finished",
                "target_date": phases[2]["end_date"],
                "deliverables": ["Working solution", "Complete dataset", "Analysis results"]
            },
            {
                "name": "Thesis Submitted",
                "description": "Final thesis document submitted",
                "target_date": phases[3]["end_date"],
                "deliverables": ["Complete thesis document", "Final submission"]
            }
        ]
        
        # Assign tasks to working days
        timeline_data = {"phases": phases, "milestones": milestones}
        return self._assign_tasks_to_days(timeline_data, user_data, start_date, deadline)
    
    def _parse_timeline_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the AI response into structured timeline data."""
        print(f"🔍 Raw AI Response (first 500 chars): {response_text[:500]}")
        
        try:
            # Clean up the response (remove markdown formatting if present)
            cleaned_text = response_text.strip()
            
            # Remove extra text before JSON
            json_start_patterns = ["```json", "```", "{"]
            for pattern in json_start_patterns:
                if pattern in cleaned_text:
                    start_idx = cleaned_text.find(pattern)
                    if pattern == "{":
                        cleaned_text = cleaned_text[start_idx:]
                        break
                    elif pattern == "```json":
                        start_idx += 7
                        cleaned_text = cleaned_text[start_idx:]
                    elif pattern == "```":
                        start_idx += 3
                        cleaned_text = cleaned_text[start_idx:]
            
            # Remove ending markdown
            if "```" in cleaned_text:
                end_idx = cleaned_text.find("```")
                if end_idx != -1:
                    cleaned_text = cleaned_text[:end_idx]
            
            # Extract JSON between first { and last }
            start_brace = cleaned_text.find("{")
            end_brace = cleaned_text.rfind("}")
            
            if start_brace != -1 and end_brace != -1 and start_brace < end_brace:
                json_text = cleaned_text[start_brace:end_brace + 1]
                
                # Fix common JSON syntax errors
                json_text = self._fix_json_syntax(json_text)
                
                print(f"🔍 Extracted JSON (first 300 chars): {json_text[:300]}")
                
                timeline_data = json.loads(json_text)
                print(f"🔍 Parsed timeline_data successfully")
                
                # Validate and process the timeline data
                validated_data = self._validate_timeline_data(timeline_data)
                return validated_data
            else:
                print("⚠️ No valid JSON braces found, creating fallback timeline")
                return self._create_fallback_timeline()
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON Parse Error: {str(e)}")
            print(f"🔍 Problematic text: {json_text[:200] if 'json_text' in locals() else cleaned_text[:200]}...")
            # Return fallback timeline instead of failing
            return self._create_fallback_timeline()
        except Exception as e:
            print(f"❌ Unexpected parsing error: {str(e)}")
            return self._create_fallback_timeline()

    def _fix_json_syntax(self, json_text: str) -> str:
        """Fix common JSON syntax errors in AI responses."""
        import re
        
        # Fix quoted strings with extra content like: "title": "Read papers" (4h),
        # Remove content in parentheses within quoted strings
        json_text = re.sub(r'"([^"]*?)\s*\([^)]*\)([^"]*?)"', r'"\1\2"', json_text)
        
        # Fix missing quotes around values like: "title": Read papers,
        json_text = re.sub(r':\s*([^",\[\]{}]+)(?=\s*[,}])', r': "\1"', json_text)
        
        # Fix trailing commas before } or ]
        json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
        
        # Fix missing commas between object properties
        json_text = re.sub(r'"\s*\n\s*"', '",\n    "', json_text)
        
        # Fix unquoted keys
        json_text = re.sub(r'(\w+):', r'"\1":', json_text)
        
        return json_text

    def _create_fallback_timeline(self) -> Dict[str, Any]:
        """Create a basic fallback timeline when parsing fails."""
        print("🔄 Creating fallback timeline")
        today = date.today()
        
        return {
            "phases": [
                {
                    "name": "Literature Review",
                    "description": "Comprehensive review of existing research",
                    "start_date": today.strftime("%Y-%m-%d"),
                    "end_date": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
                    "estimated_hours": 120,
                    "tasks": [
                        {
                            "title": "Search and collect relevant papers",
                            "description": "Use academic databases to find relevant literature",
                            "estimated_hours": 20,
                            "priority": 1,
                            "due_date": (today + timedelta(days=7)).strftime("%Y-%m-%d"),
                            "focus_sessions": 10,
                            "deliverable": "Bibliography of 20-30 papers"
                        },
                        {
                            "title": "Read and summarize key papers",
                            "description": "Read most relevant papers and create summaries",
                            "estimated_hours": 40,
                            "priority": 1,
                            "due_date": (today + timedelta(days=14)).strftime("%Y-%m-%d"),
                            "focus_sessions": 20,
                            "deliverable": "Literature summary document"
                        },
                        {
                            "title": "Identify research gaps",
                            "description": "Analyze literature to find gaps your research will address",
                            "estimated_hours": 12,
                            "priority": 2,
                            "due_date": (today + timedelta(days=21)).strftime("%Y-%m-%d"),
                            "focus_sessions": 6,
                            "deliverable": "Gap analysis document"
                        },
                        {
                            "title": "Write literature review chapter",
                            "description": "Synthesize research into coherent literature review",
                            "estimated_hours": 48,
                            "priority": 1,
                            "due_date": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
                            "focus_sessions": 24,
                            "deliverable": "Literature review chapter draft"
                        }
                    ]
                },
                {
                    "name": "Methodology Development",
                    "description": "Design and plan research methodology",
                    "start_date": (today + timedelta(days=31)).strftime("%Y-%m-%d"),
                    "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
                    "estimated_hours": 80,
                    "tasks": [
                        {
                            "title": "Define research questions",
                            "description": "Clearly articulate what your research aims to discover",
                            "estimated_hours": 8,
                            "priority": 1,
                            "due_date": (today + timedelta(days=35)).strftime("%Y-%m-%d"),
                            "focus_sessions": 4,
                            "deliverable": "Research questions document"
                        },
                        {
                            "title": "Design research methodology",
                            "description": "Choose and justify your research approach and methods",
                            "estimated_hours": 16,
                            "priority": 1,
                            "due_date": (today + timedelta(days=42)).strftime("%Y-%m-%d"),
                            "focus_sessions": 8,
                            "deliverable": "Methodology design document"
                        },
                        {
                            "title": "Set up tools and environment",
                            "description": "Install software, set up workspace, prepare tools needed",
                            "estimated_hours": 12,
                            "priority": 1,
                            "due_date": (today + timedelta(days=49)).strftime("%Y-%m-%d"),
                            "focus_sessions": 6,
                            "deliverable": "Ready development environment"
                        },
                        {
                            "title": "Write methodology chapter",
                            "description": "Document your chosen methodology and justify approach",
                            "estimated_hours": 44,
                            "priority": 1,
                            "due_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
                            "focus_sessions": 22,
                            "deliverable": "Methodology chapter draft"
                        }
                    ]
                }
            ],
            "milestones": [
                {
                    "name": "Literature Review Complete",
                    "description": "Comprehensive literature review finished",
                    "target_date": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
                    "deliverables": ["Literature review chapter", "Research gap analysis"]
                },
                {
                    "name": "Methodology Finalized",
                    "description": "Research approach and methodology confirmed",
                    "target_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
                    "deliverables": ["Methodology chapter", "Research setup complete"]
                }
            ],
            "todays_tasks": [],
            "daily_assignments": {}
        }
    
    def _validate_timeline_data(self, timeline_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean timeline data from AI response."""
        print(f"🔍 Validating timeline_data: {type(timeline_data)}")
        print(f"🔍 Input keys: {list(timeline_data.keys()) if isinstance(timeline_data, dict) else 'Not a dict'}")
        
        validated_data = {
            "phases": [],
            "milestones": []
        }
        
        # Validate phases
        phases_input = timeline_data.get("phases", [])
        print(f"🔍 Found {len(phases_input)} phases in input")
        for i, phase in enumerate(phases_input):
            print(f"🔍 Phase {i}: {list(phase.keys()) if isinstance(phase, dict) else 'Not a dict'}")
            if isinstance(phase, dict) and all(key in phase for key in ["name", "start_date", "end_date", "estimated_hours"]):
                validated_data["phases"].append(phase)
                print(f"✅ Phase {i} validated")
            else:
                print(f"⚠️ Phase {i} failed validation")
        
        # Validate milestones
        milestones_input = timeline_data.get("milestones", [])
        print(f"🔍 Found {len(milestones_input)} milestones in input")
        for i, milestone in enumerate(milestones_input):
            if isinstance(milestone, dict) and all(key in milestone for key in ["name", "target_date"]):
                validated_data["milestones"].append(milestone)
                print(f"✅ Milestone {i} validated")
            else:
                print(f"⚠️ Milestone {i} failed validation")
        
        print(f"🔍 Final validated data: {len(validated_data['phases'])} phases, {len(validated_data['milestones'])} milestones")
        return validated_data
    
    def _adjust_timeline_for_user(self, timeline_data: Dict[str, Any], 
                                 user_data: UserQuestionnaireRequest) -> Dict[str, Any]:
        """Adjust timeline based on user characteristics."""
        
        # Debug: Check what we received
        print(f"🔍 Timeline data structure: {list(timeline_data.keys()) if timeline_data else 'None'}")
        print(f"🔍 Timeline data: {str(timeline_data)[:200]}...")
        
        # Ensure timeline_data has the expected structure
        if not isinstance(timeline_data, dict):
            print("⚠️ Timeline data is not a dictionary, using fallback")
            return self._create_fallback_timeline()
        
        if "phases" not in timeline_data:
            print("⚠️ No 'phases' key in timeline data, using fallback")
            return self._create_fallback_timeline()
        
        if "milestones" not in timeline_data:
            print("⚠️ No 'milestones' key in timeline data, adding empty milestones")
            timeline_data["milestones"] = []
        
        try:
            # Apply buffer time based on procrastination level
            buffer_multiplier = {
                "low": 1.1,
                "medium": 1.15,
                "high": 1.25
            }
            
            multiplier = buffer_multiplier.get(user_data.procrastination_level.value, 1.15)
            
            # Adjust task durations
            for phase in timeline_data["phases"]:
                if "estimated_hours" in phase:
                    phase["estimated_hours"] = int(phase["estimated_hours"] * multiplier)
                
                for task in phase.get("tasks", []):
                    if "estimated_hours" in task:
                        task["estimated_hours"] = max(0.5, task["estimated_hours"] * multiplier)
            
            # Adjust milestone dates
            for milestone in timeline_data["milestones"]:
                if "target_date" in milestone:
                    try:
                        milestone_date = datetime.strptime(milestone["target_date"], "%Y-%m-%d").date()
                        adjusted_date = milestone_date + timedelta(days=int((milestone_date - date.today()).days * (multiplier - 1)))
                        milestone["target_date"] = adjusted_date.strftime("%Y-%m-%d")
                    except (ValueError, TypeError) as e:
                        print(f"⚠️ Error adjusting milestone date: {e}")
            
            return timeline_data
            
        except Exception as e:
            print(f"❌ Error adjusting timeline: {str(e)}")
            return self._create_fallback_timeline()
    
    def generate_emergency_replan(self, user_id: int, current_timeline: Dict[str, Any], 
                                 reason: str, new_constraints: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate an emergency replan when user falls behind schedule.
        
        Args:
            user_id: User ID
            current_timeline: Current timeline data
            reason: Reason for emergency replan
            new_constraints: New constraints or limitations
            
        Returns:
            Dict containing the new timeline and adjustments
        """
        replan_prompt = f"""
        EMERGENCY REPLAN REQUEST
        
        The student has fallen behind schedule and needs an emergency replan.
        
        CURRENT SITUATION:
        - Reason for replan: {reason}
        - New constraints: {json.dumps(new_constraints, indent=2)}
        
        CURRENT TIMELINE:
        {json.dumps(current_timeline, indent=2)}
        
        REQUIREMENTS:
        1. Prioritize the most critical tasks
        2. Remove or combine less important tasks
        3. Adjust timeline to be realistic with new constraints
        4. Maintain thesis quality standards
        5. Provide clear justification for changes
        
        RESPOND WITH VALID JSON:
        {{
            "new_timeline": {{
                "phases": [...],
                "milestones": [...]
            }},
            "adjustments_made": ["list of changes made"],
            "impact_analysis": {{
                "removed_tasks": ["list of removed tasks"],
                "priority_changes": ["list of priority changes"],
                "risk_assessment": "assessment of risks"
            }}
        }}
        """
        
        try:
            response_text = self.provider.generate_content(replan_prompt)
            replan_data = self._parse_timeline_response(response_text)
            return replan_data
        except Exception as e:
            raise Exception(f"Failed to generate emergency replan: {str(e)}")
    
    def generate_daily_insights(self, user_progress: Dict[str, Any]) -> str:
        """
        Generate daily insights and motivational messages.
        
        Args:
            user_progress: User's progress data
            
        Returns:
            String containing insights and motivation
        """
        insights_prompt = f"""
        Generate a personalized daily insight and motivational message for a thesis student.
        
        PROGRESS DATA:
        {json.dumps(user_progress, indent=2)}
        
        REQUIREMENTS:
        1. Analyze progress patterns
        2. Identify strengths and areas for improvement
        3. Provide specific, actionable advice
        4. Include motivational message
        5. Keep it concise and encouraging
        
        RESPOND WITH:
        A brief, motivational insight (2-3 sentences max)
        """
        
        try:
            response_text = self.provider.generate_content(insights_prompt)
            return response_text.strip()
        except Exception as e:
            return "Keep up the great work! Every step forward brings you closer to your thesis completion."
    
    def test_connection(self) -> bool:
        """Test the AI provider connection."""
        return self.provider.test_connection()
    
    def brainstorm_thesis_topic(self, message: str, conversation_history: List[Dict[str, str]], 
                               user_field: str = None) -> Dict[str, Any]:
        """
        Conduct an interactive brainstorming session to help develop thesis topic.
        
        Args:
            message: User's current message
            conversation_history: Previous conversation messages
            user_field: User's field of study (if known)
            
        Returns:
            Dict containing AI response and topic extraction
        """
        # Build conversation context
        context = self._build_brainstorming_context(conversation_history, user_field)
        
        # Count messages to determine if we should suggest finalization
        user_messages = [msg for msg in conversation_history if msg.get('role') == 'user']
        
        # Create simplified brainstorming prompt that works better with Ollama
        if len(user_messages) >= 3:  # After 3+ exchanges, start suggesting finalization
            prompt = f"""
You are an experienced academic advisor helping a student develop their thesis topic.

CONTEXT:
{context}

STUDENT'S MESSAGE: "{message}"

Based on this conversation, the student now has enough ideas to develop a clear thesis topic. 

Please provide a supportive response that:
1. Acknowledges their research direction
2. Suggests they have enough information to finalize their topic
3. Mentions specific aspects they've discussed (technologies, methods, applications)
4. Encourages them to move forward with creating their thesis proposal

Keep your response conversational and encouraging (2-3 sentences).
"""
        else:
            prompt = f"""
You are an experienced academic advisor helping a student brainstorm their thesis topic.

CONTEXT:
{context}

STUDENT'S MESSAGE: "{message}"

Please provide a supportive response that:
1. Acknowledges their interests
2. Asks ONE specific follow-up question to help them explore deeper
3. Suggests specific research angles, technologies, or methodologies when appropriate
4. Helps them think about practical implementation

Keep your response conversational and focused (2-3 sentences).
"""
        
        try:
            response_text = self.provider.generate_content(prompt)
            
            # For Ollama, we'll use a simpler approach - just return the conversational response
            # and determine topic clarity based on conversation length and content
            user_messages = [msg['content'] for msg in conversation_history if msg.get('role') == 'user']
            
            # Analyze topic clarity based on conversation content
            topic_clarity = "low"
            if len(user_messages) >= 3:
                # Check if user has mentioned specific technologies, methodologies, or applications
                all_content = " ".join(user_messages + [message]).lower()
                specific_terms = ["machine learning", "ai", "nlp", "data", "analysis", "system", "application", 
                                "algorithm", "model", "database", "web", "mobile", "healthcare", "education",
                                "security", "blockchain", "iot", "cloud", "social media", "psychology"]
                
                mentioned_terms = [term for term in specific_terms if term in all_content]
                if len(mentioned_terms) >= 2:
                    topic_clarity = "high"
                elif len(mentioned_terms) >= 1:
                    topic_clarity = "medium"
            
            return {
                "response": response_text.strip(),
                "topic_clarity": topic_clarity,
                "suggested_topic": None,  # We'll handle this in finalization
                "suggested_description": None,
                "next_question": None
            }
            
        except Exception as e:
            print(f"❌ Brainstorming error: {str(e)}")
            return {
                "response": "I'm here to help you brainstorm! What area of research interests you most?",
                "topic_clarity": "low",
                "suggested_topic": None,
                "suggested_description": None,
                "next_question": None
            }
    
    def _build_brainstorming_context(self, conversation_history: List[Dict[str, str]], 
                                   user_field: str = None) -> str:
        """Build context for brainstorming conversation."""
        context_parts = []
        
        if user_field:
            context_parts.append(f"Field of study: {user_field}")
        
        if conversation_history:
            context_parts.append("Previous conversation:")
            for msg in conversation_history[-6:]:  # Last 6 messages for context
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                context_parts.append(f"{role.capitalize()}: {content}")
        else:
            context_parts.append("This is the beginning of the conversation.")
        
        return "\n".join(context_parts)
    
    def _parse_brainstorming_response(self, response_text: str) -> Dict[str, Any]:
        """Parse AI brainstorming response."""
        try:
            # Clean up the response
            cleaned_text = response_text.strip()
            
            # Remove markdown code blocks
            if "```json" in cleaned_text:
                start_idx = cleaned_text.find("```json") + 7
                end_idx = cleaned_text.find("```", start_idx)
                if end_idx != -1:
                    cleaned_text = cleaned_text[start_idx:end_idx]
            elif "```" in cleaned_text:
                start_idx = cleaned_text.find("```") + 3
                end_idx = cleaned_text.find("```", start_idx)
                if end_idx != -1:
                    cleaned_text = cleaned_text[start_idx:end_idx]
            
            # Try to find JSON content
            start_brace = cleaned_text.find("{")
            end_brace = cleaned_text.rfind("}")
            
            if start_brace != -1 and end_brace != -1 and start_brace < end_brace:
                json_text = cleaned_text[start_brace:end_brace + 1]
                parsed_response = json.loads(json_text)
                
                # Validate required fields
                required_fields = ['response', 'topic_clarity']
                if all(field in parsed_response for field in required_fields):
                    return parsed_response
            
            # Fallback: treat entire response as conversational response
            return {
                "response": cleaned_text,
                "topic_clarity": "low",
                "suggested_topic": None,
                "suggested_description": None,
                "next_question": None
            }
            
        except json.JSONDecodeError:
            return {
                "response": cleaned_text if cleaned_text else "I'm here to help you brainstorm! What interests you?",
                "topic_clarity": "low",
                "suggested_topic": None,
                "suggested_description": None,
                "next_question": None
            }
    
    def finalize_thesis_topic(self, conversation_history: List[Dict[str, str]], 
                            user_field: str) -> Dict[str, str]:
        """
        Extract final thesis topic and description from brainstorming conversation.
        
        Args:
            conversation_history: Complete conversation history
            user_field: User's field of study
            
        Returns:
            Dict with thesis_topic and thesis_description
        """
        # Build conversation summary
        conversation_text = "\n".join([
            f"{msg.get('role', 'user').capitalize()}: {msg.get('content', '')}"
            for msg in conversation_history
        ])
        
        prompt = f"""
You are an academic advisor helping to finalize a thesis topic based on a brainstorming conversation.

FIELD OF STUDY: {user_field}

CONVERSATION SUMMARY:
{conversation_text}

Please create a clear thesis topic and detailed description based on this conversation.

TOPIC: Write a specific, focused thesis title (10-20 words) that captures the main research focus from the conversation.

DESCRIPTION: Write a comprehensive description (200-400 words) that includes:
- The specific research problem or question
- Main objectives and goals  
- Proposed methodology and approach
- Expected contributions and significance
- Any specific technologies or techniques mentioned

IMPORTANT: Use only double quotes in JSON, no triple quotes or line breaks in strings.

Format your response as valid JSON:
{{"thesis_topic": "Your specific thesis title here", "thesis_description": "Your comprehensive description here in a single line without line breaks"}}
"""
        
        try:
            response_text = self.provider.generate_content(prompt)
            print(f"🔍 Topic extraction raw response: {response_text[:200]}...")
            return self._parse_topic_extraction(response_text, conversation_history)
        except Exception as e:
            print(f"❌ Topic extraction error: {str(e)}")
            # Return fallback based on conversation
            return self._create_fallback_topic(conversation_history, user_field)
    
    def _parse_topic_extraction(self, response_text: str, conversation_history: List[Dict[str, str]]) -> Dict[str, str]:
        """Parse topic extraction response."""
        try:
            # Clean up the response
            cleaned_text = response_text.strip()
            print(f"🔍 Topic extraction raw response: {cleaned_text[:300]}...")
            
            # Remove markdown code blocks if present
            if "```json" in cleaned_text:
                start_idx = cleaned_text.find("```json") + 7
                end_idx = cleaned_text.find("```", start_idx)
                if end_idx != -1:
                    cleaned_text = cleaned_text[start_idx:end_idx]
            elif "```" in cleaned_text:
                start_idx = cleaned_text.find("```") + 3
                end_idx = cleaned_text.find("```", start_idx)
                if end_idx != -1:
                    cleaned_text = cleaned_text[start_idx:end_idx]
            
            # Fix triple quotes and multiline issues
            cleaned_text = cleaned_text.replace('"""', '"').replace("'''", '"')
            # Remove line breaks within strings
            cleaned_text = re.sub(r'"\s*\n\s*([^"]*?)\s*\n\s*"', r'"\1"', cleaned_text, flags=re.DOTALL)
            # Fix multiline descriptions
            cleaned_text = re.sub(r'"thesis_description":\s*"""([^"]*?)"""', r'"thesis_description": "\1"', cleaned_text, flags=re.DOTALL)
            cleaned_text = re.sub(r'"thesis_description":\s*"([^"]*?)\n([^"]*?)"', r'"thesis_description": "\1 \2"', cleaned_text, flags=re.DOTALL)
            
            print(f"🔧 After cleaning: {cleaned_text[:300]}...")
            
            # Extract JSON - be more flexible
            start_brace = cleaned_text.find("{")
            end_brace = cleaned_text.rfind("}")
            
            if start_brace != -1 and end_brace != -1:
                json_text = cleaned_text[start_brace:end_brace + 1]
                print(f"🔍 Extracted JSON: {json_text[:500]}...")
                
                # Try to fix common JSON issues before parsing
                json_text = json_text.replace('\n', ' ').replace('\r', ' ')
                # Fix trailing commas
                json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
                # Fix any remaining triple quotes
                json_text = json_text.replace('"""', '"')
                # Compress multiple spaces
                json_text = re.sub(r'\s+', ' ', json_text)
                
                try:
                    parsed = json.loads(json_text)
                    
                    if 'thesis_topic' in parsed and 'thesis_description' in parsed:
                        print(f"✅ Successfully parsed topic: {parsed['thesis_topic'][:100]}...")
                        return {
                            'thesis_topic': parsed['thesis_topic'].strip(),
                            'thesis_description': parsed['thesis_description'].strip()
                        }
                except json.JSONDecodeError as json_err:
                    print(f"🔧 JSON decode failed, trying to extract manually: {str(json_err)}")
                    
                    # Try to extract topic and description manually using regex
                    topic_match = re.search(r'"thesis_topic":\s*"([^"]+)"', json_text)
                    desc_match = re.search(r'"thesis_description":\s*"([^"]+)"', json_text)
                    
                    if topic_match and desc_match:
                        print(f"✅ Manual extraction successful: {topic_match.group(1)[:100]}...")
                        return {
                            'thesis_topic': topic_match.group(1).strip(),
                            'thesis_description': desc_match.group(1).strip()
                        }
                    else:
                        # Try with more flexible regex that can handle partial matches
                        topic_flexible = re.search(r'thesis_topic[^"]*"([^"]+)"', cleaned_text)
                        desc_flexible = re.search(r'thesis_description[^"]*"([^"]+)"', cleaned_text)
                        
                        if topic_flexible and desc_flexible:
                            print(f"✅ Flexible extraction successful: {topic_flexible.group(1)[:100]}...")
                            return {
                                'thesis_topic': topic_flexible.group(1).strip(),
                                'thesis_description': desc_flexible.group(1).strip()
                            }
            
            print("⚠️ JSON parsing failed, creating fallback from conversation")
            # Fallback if parsing fails
            return self._create_fallback_topic(conversation_history, "General")
            
        except Exception as e:
            print(f"❌ Unexpected parsing error: {str(e)}")
            return self._create_fallback_topic(conversation_history, "General")
    
    def _create_fallback_topic(self, conversation_history: List[Dict[str, str]], user_field: str) -> Dict[str, str]:
        """Create fallback topic from conversation using actual user messages."""
        # Extract user messages and build a topic from actual conversation
        user_messages = [msg['content'] for msg in conversation_history if msg.get('role') == 'user']
        
        if user_messages:
            # Combine all user messages to understand their interests
            all_content = " ".join(user_messages).lower()
            
            # Define keyword mappings for different research areas
            research_areas = {
                "machine learning": {
                    "keywords": ["machine learning", "ml", "ai", "artificial intelligence", "neural", "deep learning", "algorithm"],
                    "topic_template": "Machine Learning Applications in {field}",
                    "focus": "machine learning and artificial intelligence"
                },
                "data science": {
                    "keywords": ["data", "analysis", "analytics", "database", "big data", "visualization"],
                    "topic_template": "Data Analysis and Insights in {field}",
                    "focus": "data science and analytics"
                },
                "web development": {
                    "keywords": ["web", "website", "frontend", "backend", "javascript", "react", "node"],
                    "topic_template": "Web-Based Solutions for {field}",
                    "focus": "web development and digital solutions"
                },
                "mobile development": {
                    "keywords": ["mobile", "app", "android", "ios", "smartphone"],
                    "topic_template": "Mobile Application Development for {field}",
                    "focus": "mobile app development"
                },
                "healthcare": {
                    "keywords": ["health", "medical", "patient", "clinical", "diagnosis", "treatment"],
                    "topic_template": "Healthcare Technology Solutions",
                    "focus": "healthcare technology and medical applications"
                },
                "social media": {
                    "keywords": ["social", "media", "network", "facebook", "twitter", "instagram", "behavior"],
                    "topic_template": "Social Media Impact and Analysis",
                    "focus": "social media and behavioral analysis"
                },
                "security": {
                    "keywords": ["security", "cybersecurity", "encryption", "privacy", "protection"],
                    "topic_template": "Cybersecurity and Data Protection",
                    "focus": "cybersecurity and information protection"
                }
            }
            
            # Find the best matching research area
            best_match = None
            max_matches = 0
            
            for area, info in research_areas.items():
                matches = sum(1 for keyword in info["keywords"] if keyword in all_content)
                if matches > max_matches:
                    max_matches = matches
                    best_match = (area, info)
            
            if best_match and max_matches > 0:
                area_name, area_info = best_match
                topic = area_info["topic_template"].format(field=user_field)
                
                # Create a meaningful description based on their actual conversation
                last_messages = " ".join(user_messages[-3:]) if len(user_messages) >= 3 else " ".join(user_messages)
                description = f"This research project focuses on {area_info['focus']} within the field of {user_field}. Based on our discussion about {last_messages[:200]}{'...' if len(last_messages) > 200 else ''}, this project will explore innovative approaches and methodologies to address current challenges in the field. The research will investigate existing solutions, develop new frameworks or applications, and contribute meaningful insights through systematic analysis and practical implementation."
                
                return {
                    'thesis_topic': topic,
                    'thesis_description': description
                }
            else:
                # Generic fallback if no specific keywords found
                # Try to extract meaningful content from their messages
                interesting_words = []
                for msg in user_messages:
                    words = msg.split()
                    interesting_words.extend([word for word in words if len(word) > 5 and word.isalpha() and word.lower() not in ['interested', 'research', 'project', 'thesis', 'study']])
                
                main_focus = interesting_words[0] if interesting_words else "research"
                
                topic = f"{user_field} Research: {main_focus.capitalize()} Investigation"
                description = f"A comprehensive research project in {user_field} exploring {main_focus.lower()} and related concepts. Based on our brainstorming discussion, this project will investigate current methodologies, develop innovative approaches, and contribute new insights to the field. The research will involve literature review, methodology development, data collection and analysis, leading to practical applications and academic contributions."
                
                return {
                    'thesis_topic': topic,
                    'thesis_description': description
                }
        else:
            return {
                'thesis_topic': f"{user_field} Research Project",
                'thesis_description': f"A comprehensive research project in {user_field} that will contribute new insights to the field through systematic investigation and analysis. This project will explore current methodologies, develop innovative approaches, and provide significant contributions to academic knowledge through rigorous research and empirical validation."
            }


def test_ai_connection(provider: str = None) -> Dict[str, Any]:
    """
    Test the AI service connection for a specific provider.
    
    Args:
        provider: The AI provider to test ("gemini" or "ollama")
        
    Returns:
        Dict containing test results
    """
    results = {
        "gemini": False,
        "ollama": False
    }
    
    if not provider or provider == "gemini":
        try:
            if settings.GEMINI_API_KEY:
                gemini_provider = GeminiProvider()
                results["gemini"] = gemini_provider.test_connection()
        except Exception:
            results["gemini"] = False
    
    if not provider or provider == "ollama":
        try:
            ollama_provider = OllamaProvider()
            results["ollama"] = ollama_provider.test_connection()
        except Exception:
            results["ollama"] = False
    
    return results


# Global AI service instance - will use default provider from settings
ai_service = ThesisAIPlannerAgent() 