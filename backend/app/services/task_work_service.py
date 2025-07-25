#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
task_work_service.py
~~~~~~~~~~~~~~~~~~~~
Comprehensive service for managing task work sessions with AI assistance.
Integrates helper tools, ethics tracking, and deliverable management.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from uuid import uuid4

from .task_helpers.ai_detector import detect_ai_content
from .task_helpers.bibtex_generator import generate_bibtex
from .task_helpers.semantic_scholar import get_paper_metadata, search_papers
from .task_helpers.pdf_summarizer import create_pdf_summarizer
from .task_helpers.ocr import image_to_latex, is_ocr_available
from .task_helpers.ethics_system import TaskEthicsManager
from .task_helpers.grammar_checker import create_grammar_checker
from .task_helpers.web_search import create_web_search_service
from .task_helpers.wikipedia_lookup import create_wikipedia_service
from .task_helpers.survey_helper import create_survey_helper
from .task_helpers.math_solver import create_math_solver

logger = logging.getLogger(__name__)

class TaskWorkService:
    """Service for managing task work sessions with AI assistance and ethics tracking."""
    
    def __init__(self, ai_service, db_session=None):
        """
        Initialize task work service.
        
        Args:
            ai_service: AI service instance
            db_session: Database session for persistence
        """
        self.ai_service = ai_service
        self.db_session = db_session
        
        # Initialize all tool services
        self.pdf_summarizer = create_pdf_summarizer(ai_service)
        self.grammar_checker = create_grammar_checker(ai_service)
        self.web_search_service = create_web_search_service(ai_service)
        self.wikipedia_service = create_wikipedia_service(ai_service)
        self.survey_helper = create_survey_helper(ai_service)
        self.math_solver = create_math_solver(ai_service)
        
        # Session storage
        self.active_sessions = {}  # task_id -> TaskSession
        
        logger.info("TaskWorkService initialized with AI assistance and ethics tracking")
    
    def start_task_session(self, task_id: str, user_id: str, task_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start a new task work session.
        
        Args:
            task_id: Unique task identifier
            user_id: User identifier
            task_info: Information about the task (title, description, etc.)
            
        Returns:
            Session information and available tools
        """
        try:
            # Create new task session
            session = TaskSession(
                task_id=task_id,
                user_id=user_id,
                task_info=task_info,
                ai_service=self.ai_service
            )
            
            self.active_sessions[task_id] = session
            
            # Get available tools
            available_tools = self._get_available_tools()
            
            logger.info(f"Started task session for task {task_id}, user {user_id}")
            
            return {
                "success": True,
                "session_id": session.session_id,
                "task_info": task_info,
                "available_tools": available_tools,
                "welcome_message": self._generate_welcome_message(task_info),
                "ethics_summary": session.ethics_manager.ethics_tracker.get_ethics_summary()
            }
            
        except Exception as e:
            logger.error(f"Error starting task session: {e}")
            return {
                "success": False,
                "error": f"Failed to start task session: {str(e)}"
            }
    
    def process_user_message(self, task_id: str, message: str, tool_request: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process a user message in the context of a task work session.
        
        Args:
            task_id: Task identifier
            message: User's message/prompt
            tool_request: Optional tool usage request
            
        Returns:
            AI response with tool results and ethics assessment
        """
        session = self.active_sessions.get(task_id)
        if not session:
            return {
                "success": False,
                "error": "Task session not found. Please start the task first."
            }
        
        try:
            # Process the message through the session
            return session.process_message(message, tool_request)
            
        except Exception as e:
            logger.error(f"Error processing message for task {task_id}: {e}")
            return {
                "success": False,
                "error": f"Error processing message: {str(e)}"
            }
    
    def use_tool(self, task_id: str, tool_name: str, tool_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use a specific tool in the context of a task.
        
        Args:
            task_id: Task identifier
            tool_name: Name of the tool to use
            tool_params: Parameters for the tool
            
        Returns:
            Tool execution results
        """
        session = self.active_sessions.get(task_id)
        if not session:
            return {
                "success": False,
                "error": "Task session not found"
            }
        
        return session.use_tool(tool_name, tool_params)
    
    def complete_task(self, task_id: str, deliverable: str) -> Dict[str, Any]:
        """
        Complete a task and save the deliverable.
        
        Args:
            task_id: Task identifier
            deliverable: Final deliverable content
            
        Returns:
            Completion status and ethics report
        """
        session = self.active_sessions.get(task_id)
        if not session:
            return {
                "success": False,
                "error": "Task session not found"
            }
        
        try:
            # Complete the session
            completion_result = session.complete_task(deliverable)
            
            # Remove from active sessions
            del self.active_sessions[task_id]
            
            logger.info(f"Task {task_id} completed successfully")
            return completion_result
            
        except Exception as e:
            logger.error(f"Error completing task {task_id}: {e}")
            return {
                "success": False,
                "error": f"Error completing task: {str(e)}"
            }
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get current status of a task session."""
        session = self.active_sessions.get(task_id)
        if not session:
            return {
                "success": False,
                "error": "Task session not found"
            }
        
        return session.get_status()
    
    def _get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools and their descriptions."""
        tools = [
            # Original research tools
            {
                "name": "research_paper",
                "title": "Research Paper Search",
                "description": "Search for academic papers using Semantic Scholar",
                "params": ["query", "limit"],
                "example": "Find papers about machine learning in healthcare"
            },
            {
                "name": "generate_citation",
                "title": "Citation Generator",
                "description": "Generate BibTeX citations from DOI or arXiv ID",
                "params": ["identifier"],
                "example": "Generate citation for DOI: 10.1038/nature12373"
            },
            {
                "name": "ai_detection",
                "title": "AI Content Detection",
                "description": "Check if text appears to be AI-generated",
                "params": ["text"],
                "example": "Analyze this paragraph for AI generation"
            },
            {
                "name": "pdf_summary",
                "title": "PDF Summarizer", 
                "description": "Extract and summarize content from PDF files",
                "params": ["file_path", "max_chunks"],
                "example": "Summarize uploaded research paper"
            },
            
            # Writing assistance tools
            {
                "name": "grammar_check",
                "title": "Grammar & Style Checker",
                "description": "Check grammar, style, and academic writing quality",
                "params": ["text", "check_type"],
                "example": "Check this paragraph for grammar and style issues"
            },
            
            # Web research tools
            {
                "name": "web_search",
                "title": "Web Search",
                "description": "Search the web for current information and facts",
                "params": ["query", "result_count"],
                "example": "Search for recent developments in quantum computing"
            },
            {
                "name": "fact_check",
                "title": "Fact Checker",
                "description": "Verify claims and check facts with web sources",
                "params": ["claim"],
                "example": "Fact-check: COVID-19 vaccines contain microchips"
            },
            {
                "name": "source_verify",
                "title": "Source Credibility Checker",
                "description": "Assess the credibility and reliability of sources",
                "params": ["url"],
                "example": "Check credibility of news article URL"
            },
            
            # Wikipedia tools
            {
                "name": "wikipedia_search",
                "title": "Wikipedia Search",
                "description": "Search Wikipedia for background information",
                "params": ["query", "limit"],
                "example": "Search Wikipedia for information about neural networks"
            },
            {
                "name": "wikipedia_summary",
                "title": "Wikipedia Article Summary",
                "description": "Get detailed summary of Wikipedia articles",
                "params": ["title", "sentences"],
                "example": "Get summary of 'Artificial Intelligence' Wikipedia article"
            },
            {
                "name": "topic_overview",
                "title": "Topic Overview",
                "description": "Get comprehensive overview of research topics",
                "params": ["topic"],
                "example": "Get overview of machine learning topic"
            },
            
            # Survey and data collection tools
            {
                "name": "survey_questions",
                "title": "Survey Question Generator",
                "description": "Generate survey questions for research",
                "params": ["research_topic", "question_count"],
                "example": "Generate 10 survey questions about user experience"
            },
            {
                "name": "data_collection_plan",
                "title": "Data Collection Planner",
                "description": "Create comprehensive data collection plans",
                "params": ["research_objective", "target_population"],
                "example": "Plan data collection for studying student behavior"
            },
            
            # Mathematical tools
            {
                "name": "solve_equation",
                "title": "Equation Solver",
                "description": "Solve mathematical equations step-by-step",
                "params": ["equation", "variable"],
                "example": "Solve: 2x + 5 = 15 for x"
            },
            {
                "name": "calculate",
                "title": "Expression Calculator",
                "description": "Calculate complex mathematical expressions",
                "params": ["expression"],
                "example": "Calculate: sin(π/4) + log(10)"
            },
            {
                "name": "convert_units",
                "title": "Unit Converter",
                "description": "Convert between different units of measurement",
                "params": ["value", "from_unit", "to_unit"],
                "example": "Convert 100 celsius to fahrenheit"
            },
            {
                "name": "statistics",
                "title": "Statistics Calculator",
                "description": "Calculate statistical measures from data",
                "params": ["data", "statistic"],
                "example": "Calculate mean and standard deviation of [1,2,3,4,5]"
            }
        ]
        
        # Add OCR tool if available
        if is_ocr_available():
            tools.append({
                "name": "image_to_latex",
                "title": "Image to LaTeX",
                "description": "Convert mathematical equations in images to LaTeX",
                "params": ["image_path"],
                "example": "Convert this equation image to LaTeX code"
            })
        
        return tools
    
    def _generate_welcome_message(self, task_info: Dict[str, Any]) -> str:
        """Generate a personalized welcome message for the task."""
        task_title = task_info.get("title", "your task")
        task_description = task_info.get("description", "")
        
        message = f"""Welcome to your task work session! 🎯

**Task:** {task_title}

I'm here to help you work on this task using various AI-powered tools while maintaining academic integrity. Here's how I can assist:

📚 **Research Tools:** Search for papers, generate citations
🔍 **Analysis Tools:** Check for AI content, summarize PDFs  
📝 **Writing Support:** Help with structure, analysis, and understanding
🧮 **Technical Tools:** Convert equations from images to LaTeX

**Remember:** I'm here to support your learning and thinking, not to replace it. Let's work together to complete this task effectively and ethically!

What would you like to start with?"""

        return message


class TaskSession:
    """Individual task work session with conversation history and deliverable tracking."""
    
    def __init__(self, task_id: str, user_id: str, task_info: Dict[str, Any], ai_service):
        """Initialize task session."""
        self.session_id = str(uuid4())
        self.task_id = task_id
        self.user_id = user_id
        self.task_info = task_info
        self.ai_service = ai_service
        
        # Session state
        self.conversation_history = []
        self.tool_usage = []
        self.deliverable = ""
        self.is_completed = False
        self.created_at = datetime.now()
        
        # Ethics tracking
        self.ethics_manager = TaskEthicsManager(task_id, user_id, ai_service)
        
        # Helper services
        self.pdf_summarizer = create_pdf_summarizer(ai_service)
    
    def process_message(self, message: str, tool_request: Optional[Dict] = None) -> Dict[str, Any]:
        """Process a user message with ethics tracking and AI response."""
        try:
            # Ethics evaluation
            task_context = f"Task: {self.task_info.get('title', '')} - {self.task_info.get('description', '')}"
            ethics_eval = self.ethics_manager.evaluate_task_prompt(message, task_context)
            
            # Tool usage if requested
            tool_result = None
            if tool_request:
                tool_result = self.use_tool(tool_request["tool"], tool_request.get("params", {}))
            
            # Generate AI response
            ai_response = self._generate_ai_response(message, tool_result, ethics_eval)
            
            # Record conversation
            self.conversation_history.append({
                "timestamp": datetime.now(),
                "user_message": message,
                "ai_response": ai_response,
                "ethics_eval": ethics_eval,
                "tool_result": tool_result
            })
            
            # Check for intervention
            response_data = {
                "success": True,
                "ai_response": ai_response,
                "ethics_score": ethics_eval["ethical_score"],
                "ethics_reasoning": ethics_eval["reasoning"]
            }
            
            if ethics_eval["intervention_needed"]:
                response_data["intervention"] = {
                    "needed": True,
                    "message": ethics_eval["intervention_message"]
                }
            
            if tool_result:
                response_data["tool_result"] = tool_result
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "success": False,
                "error": f"Error processing message: {str(e)}"
            }
    
    def _generate_ai_response(self, message: str, tool_result: Optional[Dict], ethics_eval: Dict) -> str:
        """Generate AI response considering context, tools, and ethics."""
        # Build context
        context_parts = [
            f"You are helping a student work on their thesis task: {self.task_info.get('title', 'Unknown task')}",
            f"Task description: {self.task_info.get('description', 'No description')}",
            "Your role is to guide, support, and provide tools, but NOT to do the work for them.",
            "Encourage critical thinking, analysis, and their own insights."
        ]
        
        # Add tool result context
        if tool_result and tool_result.get("success"):
            context_parts.append(f"Tool result available: {tool_result.get('summary', 'Tool executed successfully')}")
        
        # Add ethics context if needed
        if ethics_eval["ethical_score"] < 0.6:
            context_parts.append("IMPORTANT: Guide the user toward more ethical use of AI assistance.")
        
        context = "\n".join(context_parts)
        
        # Build prompt
        prompt = f"""{context}

Student's request: {message}

Provide a helpful, educational response that supports their learning. If tool results are available, help them interpret and apply the findings to their work."""
        
        try:
            if self.ai_service and hasattr(self.ai_service, 'provider'):
                response = self.ai_service.provider.generate_content(prompt)
                return response.strip() if response else "I'm ready to help with your task."
            else:
                return "I'm here to help you with your task. How can I assist you today?"
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return "I'm here to help with your task. Please let me know what you need assistance with."
    
    def use_tool(self, tool_name: str, tool_params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific tool."""
        try:
            result = None
            
            if tool_name == "research_paper":
                query = tool_params.get("query", "")
                limit = tool_params.get("limit", 5)
                papers = search_papers(query, limit)
                result = {
                    "tool": "research_paper",
                    "query": query,
                    "papers_found": len(papers),
                    "papers": papers[:limit],
                    "summary": f"Found {len(papers)} papers for query: {query}"
                }
                
            elif tool_name == "generate_citation":
                identifier = tool_params.get("identifier", "")
                try:
                    citation = generate_bibtex(identifier)
                    result = {
                        "tool": "generate_citation",
                        "identifier": identifier,
                        "citation": citation,
                        "summary": f"Generated BibTeX citation for {identifier}"
                    }
                except Exception as e:
                    result = {
                        "tool": "generate_citation", 
                        "identifier": identifier,
                        "error": str(e),
                        "summary": f"Failed to generate citation: {str(e)}"
                    }
                    
            elif tool_name == "ai_detection":
                text = tool_params.get("text", "")
                probability, explanation = detect_ai_content(text)
                result = {
                    "tool": "ai_detection",
                    "text_length": len(text),
                    "ai_probability": probability,
                    "explanation": explanation,
                    "summary": f"AI detection: {probability:.1%} probability ({explanation})"
                }
                
            elif tool_name == "pdf_summary":
                file_path = tool_params.get("file_path", "")
                max_chunks = tool_params.get("max_chunks", 5)
                summary, status = self.pdf_summarizer.pdf_to_summary(
                    file_path, 
                    max_chunks=max_chunks
                )
                result = {
                    "tool": "pdf_summary",
                    "file_path": file_path,
                    "summary": summary,
                    "status": status,
                    "summary": f"PDF summarized: {status}"
                }
                
            elif tool_name == "image_to_latex" and is_ocr_available():
                image_path = tool_params.get("image_path", "")
                latex_code, status = image_to_latex(image_path)
                result = {
                    "tool": "image_to_latex",
                    "image_path": image_path,
                    "latex_code": latex_code,
                    "status": status,
                    "summary": f"Image OCR: {status}"
                }
            
            # New tools
            elif tool_name == "grammar_check":
                from .task_helpers.grammar_checker import check_grammar_and_style
                text = tool_params.get("text", "")
                check_type = tool_params.get("check_type", "comprehensive")
                analysis = check_grammar_and_style(text, self.ai_service, check_type)
                result = {
                    "tool": "grammar_check",
                    "analysis": analysis,
                    "summary": f"Grammar analysis: {len(analysis.get('issues', []))} issues found"
                }
            
            elif tool_name == "web_search":
                from .task_helpers.web_search import search_web
                query = tool_params.get("query", "")
                result_count = tool_params.get("result_count", 5)
                search_results = search_web(query, self.ai_service, result_count)
                result = {
                    "tool": "web_search",
                    "search_results": search_results,
                    "summary": f"Found {len(search_results.get('results', []))} web results"
                }
            
            elif tool_name == "fact_check":
                from .task_helpers.web_search import fact_check
                claim = tool_params.get("claim", "")
                fact_result = fact_check(claim, self.ai_service)
                result = {
                    "tool": "fact_check",
                    "fact_check": fact_result,
                    "summary": f"Fact-check: {fact_result.get('assessment', 'Unknown')}"
                }
            
            elif tool_name == "source_verify":
                from .task_helpers.web_search import verify_source
                url = tool_params.get("url", "")
                verification = verify_source(url, self.ai_service)
                result = {
                    "tool": "source_verify",
                    "verification": verification,
                    "summary": f"Credibility score: {verification.get('credibility_score', 0)}/10"
                }
            
            elif tool_name == "wikipedia_search":
                from .task_helpers.wikipedia_lookup import search_wikipedia
                query = tool_params.get("query", "")
                limit = tool_params.get("limit", 5)
                wiki_results = search_wikipedia(query, self.ai_service, limit)
                result = {
                    "tool": "wikipedia_search",
                    "search_results": wiki_results,
                    "summary": f"Found {wiki_results.get('total_found', 0)} Wikipedia articles"
                }
            
            elif tool_name == "wikipedia_summary":
                from .task_helpers.wikipedia_lookup import get_article_summary
                title = tool_params.get("title", "")
                sentences = tool_params.get("sentences", 3)
                summary = get_article_summary(title, self.ai_service, sentences)
                result = {
                    "tool": "wikipedia_summary",
                    "article_summary": summary,
                    "summary": f"Wikipedia summary for: {title}"
                }
            
            elif tool_name == "topic_overview":
                from .task_helpers.wikipedia_lookup import get_topic_overview
                topic = tool_params.get("topic", "")
                overview = get_topic_overview(topic, self.ai_service)
                result = {
                    "tool": "topic_overview",
                    "topic_overview": overview,
                    "summary": f"Comprehensive overview of: {topic}"
                }
            
            elif tool_name == "survey_questions":
                from .task_helpers.survey_helper import generate_survey_questions
                research_topic = tool_params.get("research_topic", "")
                question_count = tool_params.get("question_count", 10)
                questions = generate_survey_questions(research_topic, self.ai_service, question_count)
                result = {
                    "tool": "survey_questions",
                    "survey_questions": questions,
                    "summary": f"Generated {len(questions.get('questions', []))} survey questions"
                }
            
            elif tool_name == "data_collection_plan":
                from .task_helpers.survey_helper import create_data_collection_plan
                research_objective = tool_params.get("research_objective", "")
                target_population = tool_params.get("target_population", "")
                sample_size = tool_params.get("sample_size", None)
                plan = create_data_collection_plan(research_objective, target_population, self.ai_service, sample_size)
                result = {
                    "tool": "data_collection_plan",
                    "collection_plan": plan,
                    "summary": f"Created data collection plan for {target_population}"
                }
            
            elif tool_name == "solve_equation":
                from .task_helpers.math_solver import solve_equation
                equation = tool_params.get("equation", "")
                variable = tool_params.get("variable", "x")
                solution = solve_equation(equation, self.ai_service, variable)
                result = {
                    "tool": "solve_equation",
                    "solution": solution,
                    "summary": f"Solved equation for {variable}: {solution.get('solution', 'No solution')}"
                }
            
            elif tool_name == "calculate":
                from .task_helpers.math_solver import calculate_expression
                expression = tool_params.get("expression", "")
                calculation = calculate_expression(expression, self.ai_service)
                result = {
                    "tool": "calculate",
                    "calculation": calculation,
                    "summary": f"Result: {calculation.get('result', 'Error')}"
                }
            
            elif tool_name == "convert_units":
                from .task_helpers.math_solver import convert_units
                value = tool_params.get("value", 0)
                from_unit = tool_params.get("from_unit", "")
                to_unit = tool_params.get("to_unit", "")
                conversion = convert_units(float(value), from_unit, to_unit, self.ai_service)
                result = {
                    "tool": "convert_units",
                    "conversion": conversion,
                    "summary": conversion.get("conversion_string", "Conversion failed")
                }
            
            elif tool_name == "statistics":
                from .task_helpers.math_solver import solve_statistics
                data = tool_params.get("data", [])
                statistic = tool_params.get("statistic", "all")
                stats = solve_statistics(data, self.ai_service, statistic)
                result = {
                    "tool": "statistics",
                    "statistics": stats,
                    "summary": f"Calculated statistics for {stats.get('data_count', 0)} data points"
                }
                
            else:
                result = {
                    "tool": tool_name,
                    "error": f"Unknown or unavailable tool: {tool_name}",
                    "summary": f"Tool {tool_name} not available"
                }
            
            # Record tool usage
            if result:
                self.tool_usage.append({
                    "timestamp": datetime.now(),
                    "tool": tool_name,
                    "params": tool_params,
                    "result": result
                })
                
                result["success"] = "error" not in result
                return result
            
        except Exception as e:
            logger.error(f"Error using tool {tool_name}: {e}")
            return {
                "success": False,
                "tool": tool_name,
                "error": str(e),
                "summary": f"Tool error: {str(e)}"
            }
    
    def complete_task(self, deliverable: str) -> Dict[str, Any]:
        """Complete the task with final deliverable."""
        self.deliverable = deliverable
        self.is_completed = True
        
        # Get ethics report
        ethics_report = self.ethics_manager.get_task_ethics_report()
        
        # Analyze deliverable for AI content
        ai_prob, ai_explanation = detect_ai_content(deliverable)
        
        return {
            "success": True,
            "task_id": self.task_id,
            "session_id": self.session_id,
            "deliverable": deliverable,
            "deliverable_analysis": {
                "ai_probability": ai_prob,
                "ai_explanation": ai_explanation,
                "word_count": len(deliverable.split()),
                "character_count": len(deliverable)
            },
            "session_summary": {
                "duration": (datetime.now() - self.created_at).total_seconds() / 60,  # minutes
                "messages_exchanged": len(self.conversation_history),
                "tools_used": len(self.tool_usage),
                "ethics_report": ethics_report
            }
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current session status."""
        return {
            "session_id": self.session_id,
            "task_id": self.task_id,
            "is_completed": self.is_completed,
            "messages": len(self.conversation_history),
            "tools_used": len(self.tool_usage),
            "ethics_summary": self.ethics_manager.ethics_tracker.get_ethics_summary(),
            "created_at": self.created_at.isoformat()
        } 