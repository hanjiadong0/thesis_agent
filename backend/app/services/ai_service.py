"""
AI Service for timeline generation and planning.

This module handles AI-powered thesis timeline generation, task breakdown,
and intelligent planning using Gemini and smolagent.

Author: Thesis Helper Team
Date: 2024
"""

import json
import google.generativeai as genai
from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta

from backend.app.core.config import settings
from backend.app.models.schemas import UserQuestionnaireRequest, ThesisField


class ThesisAIPlannerAgent:
    """
    AI agent for thesis planning and timeline generation.
    
    This class uses Gemini AI to generate personalized thesis timelines
    based on user preferences, thesis requirements, and productivity patterns.
    """
    
    def __init__(self):
        """Initialize the AI service with Gemini configuration."""
        # Configure Gemini
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.AI_MODEL)
        
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
        Generate a personalized thesis timeline based on user data.
        
        Args:
            user_data: User questionnaire responses
            thesis_description: Detailed thesis description from partner
            
        Returns:
            Dict containing the complete timeline with tasks and milestones
        """
        # Calculate available time
        total_days = (user_data.thesis_deadline - date.today()).days
        working_days = (total_days * user_data.work_days_per_week) // 7
        total_hours = working_days * user_data.daily_hours_available
        
        # Get field-specific knowledge
        field_info = self.field_knowledge.get(user_data.thesis_field.value, 
                                             self.field_knowledge["Computer Science"])
        
        # Generate timeline using AI
        timeline_prompt = self._create_timeline_prompt(user_data, thesis_description, field_info, total_hours)
        
        try:
            response = self.model.generate_content(timeline_prompt)
            timeline_data = self._parse_timeline_response(response.text)
            
            # Add buffer time and adjust based on user characteristics
            timeline_data = self._adjust_timeline_for_user(timeline_data, user_data)
            
            return {
                "timeline": timeline_data,
                "metadata": {
                    "total_days": total_days,
                    "working_days": working_days,
                    "total_hours": total_hours,
                    "field": user_data.thesis_field.value,
                    "generated_at": datetime.utcnow().isoformat(),
                    "buffer_applied": settings.DEFAULT_BUFFER_TIME
                }
            }
        except Exception as e:
            raise Exception(f"Failed to generate timeline: {str(e)}")
    
    def _create_timeline_prompt(self, user_data: UserQuestionnaireRequest, 
                               thesis_description: str, field_info: Dict, 
                               total_hours: int) -> str:
        """Create a detailed prompt for timeline generation."""
        
        prompt = f"""
        You are an expert thesis advisor specializing in {user_data.thesis_field.value}. 
        Create a detailed, personalized timeline for this thesis project.

        STUDENT PROFILE:
        - Name: {user_data.name}
        - Field: {user_data.thesis_field.value}
        - Thesis Topic: {user_data.thesis_topic}
        - Deadline: {user_data.thesis_deadline}
        - Available Hours/Day: {user_data.daily_hours_available}
        - Work Days/Week: {user_data.work_days_per_week}
        - Total Available Hours: {total_hours}
        - Focus Duration: {user_data.focus_duration} minutes
        - Procrastination Level: {user_data.procrastination_level.value}
        - Writing Style: {user_data.writing_style.value}

        THESIS DESCRIPTION:
        {thesis_description}

        FIELD-SPECIFIC PHASES:
        {json.dumps(field_info["typical_phases"], indent=2)}

        REQUIREMENTS:
        1. Break down the thesis into specific phases with realistic time estimates
        2. Create daily tasks that fit the user's focus duration ({user_data.focus_duration} minutes)
        3. Account for procrastination level: {user_data.procrastination_level.value}
        4. Adjust for writing style: {user_data.writing_style.value}
        5. Include specific milestones and deadlines
        6. Make tasks actionable and measurable

        RESPOND WITH VALID JSON:
        {{
            "phases": [
                {{
                    "name": "Phase Name",
                    "description": "Phase description",
                    "start_date": "YYYY-MM-DD",
                    "end_date": "YYYY-MM-DD",
                    "estimated_hours": number,
                    "tasks": [
                        {{
                            "title": "Task title",
                            "description": "Task description",
                            "estimated_hours": number,
                            "priority": 1-5,
                            "due_date": "YYYY-MM-DD",
                            "dependencies": ["task_id"]
                        }}
                    ]
                }}
            ],
            "milestones": [
                {{
                    "name": "Milestone name",
                    "description": "Milestone description",
                    "target_date": "YYYY-MM-DD",
                    "deliverables": ["deliverable1", "deliverable2"]
                }}
            ]
        }}
        """
        
        return prompt
    
    def _parse_timeline_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the AI response into structured timeline data."""
        print(f"🔍 Raw AI Response (first 500 chars): {response_text[:500]}")
        
        try:
            # Clean up the response (remove markdown formatting if present)
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
            
            # Try to find JSON content between curly braces
            start_brace = cleaned_text.find("{")
            end_brace = cleaned_text.rfind("}")
            
            if start_brace != -1 and end_brace != -1 and start_brace < end_brace:
                json_text = cleaned_text[start_brace:end_brace + 1]
                print(f"🔍 Extracted JSON (first 300 chars): {json_text[:300]}")
                
                timeline_data = json.loads(json_text)
                
                # Validate and process the timeline data
                return self._validate_timeline_data(timeline_data)
            else:
                # Fallback: create a basic timeline structure
                print("⚠️ No valid JSON found, creating fallback timeline")
                return self._create_fallback_timeline()
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON Parse Error: {str(e)}")
            print(f"🔍 Problematic text: {cleaned_text[:200]}...")
            # Return fallback timeline instead of failing
            return self._create_fallback_timeline()
        except Exception as e:
            print(f"❌ Unexpected parsing error: {str(e)}")
            return self._create_fallback_timeline()
    
    def _create_fallback_timeline(self) -> Dict[str, Any]:
        """Create a basic fallback timeline when AI parsing fails."""
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
                            "estimated_hours": 40,
                            "priority": 1,
                            "due_date": (today + timedelta(days=10)).strftime("%Y-%m-%d"),
                            "dependencies": []
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
                            "title": "Design research approach",
                            "description": "Define methodology and approach",
                            "estimated_hours": 40,
                            "priority": 1,
                            "due_date": (today + timedelta(days=45)).strftime("%Y-%m-%d"),
                            "dependencies": []
                        }
                    ]
                },
                {
                    "name": "Implementation",
                    "description": "Execute the research plan",
                    "start_date": (today + timedelta(days=61)).strftime("%Y-%m-%d"),
                    "end_date": (today + timedelta(days=120)).strftime("%Y-%m-%d"),
                    "estimated_hours": 200,
                    "tasks": [
                        {
                            "title": "Begin implementation",
                            "description": "Start executing the research plan",
                            "estimated_hours": 100,
                            "priority": 1,
                            "due_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
                            "dependencies": []
                        }
                    ]
                },
                {
                    "name": "Writing and Finalization",
                    "description": "Write and finalize thesis document",
                    "start_date": (today + timedelta(days=121)).strftime("%Y-%m-%d"),
                    "end_date": (today + timedelta(days=180)).strftime("%Y-%m-%d"),
                    "estimated_hours": 150,
                    "tasks": [
                        {
                            "title": "Write thesis chapters",
                            "description": "Write main thesis content",
                            "estimated_hours": 100,
                            "priority": 1,
                            "due_date": (today + timedelta(days=160)).strftime("%Y-%m-%d"),
                            "dependencies": []
                        }
                    ]
                }
            ],
            "milestones": [
                {
                    "name": "Literature Review Complete",
                    "description": "Complete comprehensive literature review",
                    "target_date": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
                    "deliverables": ["Literature review chapter"]
                },
                {
                    "name": "Methodology Finalized",
                    "description": "Research methodology completed and approved",
                    "target_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
                    "deliverables": ["Methodology chapter"]
                },
                {
                    "name": "Implementation Complete",
                    "description": "All research implementation finished",
                    "target_date": (today + timedelta(days=120)).strftime("%Y-%m-%d"),
                    "deliverables": ["Implementation results"]
                },
                {
                    "name": "Thesis Submitted",
                    "description": "Final thesis submitted",
                    "target_date": (today + timedelta(days=180)).strftime("%Y-%m-%d"),
                    "deliverables": ["Complete thesis document"]
                }
            ]
        }
    
    def _validate_timeline_data(self, timeline_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean timeline data from AI response."""
        validated_data = {
            "phases": [],
            "milestones": []
        }
        
        # Validate phases
        for phase in timeline_data.get("phases", []):
            if all(key in phase for key in ["name", "start_date", "end_date", "estimated_hours"]):
                validated_data["phases"].append(phase)
        
        # Validate milestones
        for milestone in timeline_data.get("milestones", []):
            if all(key in milestone for key in ["name", "target_date"]):
                validated_data["milestones"].append(milestone)
        
        return validated_data
    
    def _adjust_timeline_for_user(self, timeline_data: Dict[str, Any], 
                                 user_data: UserQuestionnaireRequest) -> Dict[str, Any]:
        """Adjust timeline based on user characteristics."""
        
        # Apply buffer time based on procrastination level
        buffer_multiplier = {
            "low": 1.1,
            "medium": 1.15,
            "high": 1.25
        }
        
        multiplier = buffer_multiplier.get(user_data.procrastination_level.value, 1.15)
        
        # Adjust task durations
        for phase in timeline_data["phases"]:
            phase["estimated_hours"] = int(phase["estimated_hours"] * multiplier)
            
            for task in phase.get("tasks", []):
                task["estimated_hours"] = max(0.5, task["estimated_hours"] * multiplier)
        
        # Adjust milestone dates
        for milestone in timeline_data["milestones"]:
            milestone_date = datetime.strptime(milestone["target_date"], "%Y-%m-%d").date()
            adjusted_date = milestone_date + timedelta(days=int((milestone_date - date.today()).days * (multiplier - 1)))
            milestone["target_date"] = adjusted_date.strftime("%Y-%m-%d")
        
        return timeline_data
    
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
            response = self.model.generate_content(replan_prompt)
            replan_data = self._parse_timeline_response(response.text)
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
            response = self.model.generate_content(insights_prompt)
            return response.text.strip()
        except Exception as e:
            return "Keep up the great work! Every step forward brings you closer to your thesis completion."


def test_ai_connection() -> bool:
    """
    Test the AI service connection.
    
    Returns:
        bool: True if connection is successful
    """
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(settings.AI_MODEL)
        response = model.generate_content("Test connection")
        return True
    except Exception:
        return False


# Global AI service instance
ai_service = ThesisAIPlannerAgent() 