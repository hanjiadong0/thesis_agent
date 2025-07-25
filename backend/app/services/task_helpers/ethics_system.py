#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ethics_system.py
~~~~~~~~~~~~~~~~
Ethical AI usage tracking and intervention system.
Adapted for the thesis helper system to work with our AI service and database.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import re

try:
    import pandas as pd
    import numpy as np
    from scipy.spatial import distance
    SCIENTIFIC_LIBRARIES_AVAILABLE = True
except ImportError:
    SCIENTIFIC_LIBRARIES_AVAILABLE = False
    pd = None
    np = None
    distance = None

try:
    import torch
    from transformers import AutoModel, AutoTokenizer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    torch = None
    AutoModel = None
    AutoTokenizer = None

logger = logging.getLogger(__name__)

class EthicsTracker:
    """Ethics tracking and intervention system for AI usage in academic contexts."""
    
    def __init__(self, ai_service=None, db_session=None):
        """
        Initialize ethics tracker.
        
        Args:
            ai_service: AI service instance for ethical assessment
            db_session: Database session for persistence
        """
        self.ai_service = ai_service
        self.db_session = db_session
        
        # Ethics configuration
        self.ethical_threshold = 0.4  # Below this is considered unethical
        self.intervention_streak = 3  # Trigger intervention after this many unethical prompts
        self.trust_decay_rate = 2.5  # How fast trust decreases for unethical behavior
        self.trust_recovery_rate = 0.5  # How slowly trust recovers
        
        # In-memory tracking for current session
        self.session_scores = []
        self.session_prompts = []
        self.current_trust_level = 0.8
        self.unethical_streak = 0
        
        # Initialize embedding model if available
        self.embedding_model = None
        self.embedding_tokenizer = None
        if EMBEDDINGS_AVAILABLE:
            self._initialize_embeddings()
    
    def _initialize_embeddings(self):
        """Initialize the Jina embedding model for similarity search."""
        try:
            model_name = "jinaai/jina-embeddings-v3"
            self.embedding_tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.embedding_model = AutoModel.from_pretrained(model_name, trust_remote_code=True)
            
            if torch.cuda.is_available():
                self.embedding_model = self.embedding_model.cuda()
            
            logger.info("Jina embedding model loaded for ethics tracking")
        except Exception as e:
            logger.warning(f"Could not load embedding model: {e}")
            self.embedding_model = None
            self.embedding_tokenizer = None
    
    def assess_ethical_usage(self, prompt: str, context: str = "") -> Tuple[float, str]:
        """
        Assess the ethical implications of a user prompt.
        
        Args:
            prompt: The user's prompt to assess
            context: Additional context about the task
            
        Returns:
            Tuple of (ethical_score, ethical_reasoning)
        """
        if not self.ai_service:
            return 0.5, "AI service not available for ethical assessment"
        
        try:
            # Create ethical assessment prompt
            assessment_prompt = f"""You are an academic ethics reviewer evaluating whether a user's prompt is ethically appropriate for use with AI in academic contexts. Be critical, impartial, and apply strict standards of academic integrity.

Classify the prompt as one of:
- "Ethical": supports responsible inquiry, learning, and dignity
- "Neutral": technically safe, but not ethically meaningful  
- "Unethical": promotes deception, manipulation, harm, or dishonesty

You MUST respond using the following JSON structure:
{{
    "intent": "<brief description of what user wants>",
    "ethical_classification": "Ethical" | "Neutral" | "Unethical",
    "ethical_score": <float between 0.0 (very unethical) and 1.0 (fully ethical)>,
    "ethical_reasoning": "<1-3 sentence explanation>"
}}

Examples:
- "Can you help me outline my thesis structure?" → Ethical (0.95): Supports self-led work and critical thinking
- "Write my full literature review with citations" → Unethical (0.25): Delegates core authorship and misuses AI
- "Summarize this article for me" → Ethical (0.9): Supports comprehension with responsible guidance

Context: {context}
Prompt to evaluate: {prompt}

Evaluate its ethical implications:"""

            # Use our AI service
            if self.ai_service and hasattr(self.ai_service, 'provider'):
                response = self.ai_service.provider.generate_content(assessment_prompt)
            else:
                return 0.5, "AI service not available for ethical assessment"
            
            # Parse JSON response
            return self._parse_ethical_assessment(response)
            
        except Exception as e:
            logger.error(f"Error in ethical assessment: {e}")
            return 0.5, f"Error during ethical assessment: {str(e)}"
    
    def _parse_ethical_assessment(self, response: str) -> Tuple[float, str]:
        """Parse the AI's ethical assessment response."""
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                assessment = json.loads(json_str)
                
                score = assessment.get("ethical_score", 0.5)
                reasoning = assessment.get("ethical_reasoning", "Assessment completed")
                
                return float(score), reasoning
            else:
                # Fallback: try to extract score from text
                score_match = re.search(r'(\d+\.?\d*)', response)
                if score_match:
                    score = min(1.0, max(0.0, float(score_match.group(1))))
                    return score, "Ethical assessment completed"
                else:
                    return 0.5, "Could not parse ethical assessment"
                    
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Could not parse ethical assessment: {e}")
            return 0.5, "Failed to parse ethical assessment"
    
    def update_ethics_state(self, prompt: str, ethical_score: float, context: str = ""):
        """
        Update the user's ethical state based on new prompt.
        
        Args:
            prompt: The user's prompt
            ethical_score: Ethical score (0-1)
            context: Additional context
        """
        # Add to session tracking
        self.session_scores.append(ethical_score)
        self.session_prompts.append({
            "prompt": prompt,
            "score": ethical_score,
            "timestamp": datetime.now(),
            "context": context
        })
        
        # Update trust level
        if ethical_score < self.ethical_threshold:
            # Penalty for unethical behavior
            penalty = (self.ethical_threshold - ethical_score) * self.trust_decay_rate
            self.current_trust_level -= penalty
            self.unethical_streak += 1
        else:
            # Recovery for ethical behavior
            gain = (ethical_score - self.ethical_threshold) * self.trust_recovery_rate
            self.current_trust_level += gain
            self.unethical_streak = 0
        
        # Clamp trust level between 0 and 1
        self.current_trust_level = max(0.0, min(1.0, self.current_trust_level))
        
        logger.info(f"Ethics state updated: score={ethical_score:.2f}, trust={self.current_trust_level:.2f}, streak={self.unethical_streak}")
    
    def should_trigger_intervention(self) -> bool:
        """Check if an intervention should be triggered."""
        return (
            self.unethical_streak >= self.intervention_streak or 
            self.current_trust_level < self.ethical_threshold
        )
    
    def generate_intervention_message(self) -> str:
        """Generate an intervention message using AI."""
        if not self.ai_service:
            return "Please remember to use AI responsibly and maintain academic integrity."
        
        # Get recent unethical prompts
        recent_unethical = [
            p for p in self.session_prompts[-10:] 
            if p["score"] < self.ethical_threshold
        ]
        
        context_info = ""
        if recent_unethical:
            latest = recent_unethical[-1]
            context_info = f"Your most recent concerning prompt was: \"{latest['prompt']}\"\n"
        
        context_info += f"Your current trust level is {self.current_trust_level:.2f}.\n"
        context_info += f"You have an unethical streak of {self.unethical_streak}.\n"
        
        intervention_prompt = f"""Based on recent interactions and ethical usage score, an intervention is suggested.

{context_info}

Please provide a kind, supportive, and encouraging message to the user. Gently remind them about the importance of academic integrity and using AI responsibly as a tool to assist their own learning and work, rather than replacing their effort. Suggest they rephrase their requests to focus on brainstorming, analysis, or understanding concepts. Avoid any judgmental or punitive language. Focus on helping them learn and improve their ethical AI usage.

Your supportive suggestion:"""

        try:
            if self.ai_service and hasattr(self.ai_service, 'provider'):
                response = self.ai_service.provider.generate_content(intervention_prompt)
                return response.strip() if response else "Please remember to use AI ethically in your academic work."
            else:
                return "Please use AI as a learning tool to enhance your understanding, not to replace your own work and thinking."
            
        except Exception as e:
            logger.error(f"Error generating intervention: {e}")
            return "Please remember to use AI responsibly and maintain academic integrity in your academic work."
    
    def get_ethics_summary(self) -> Dict[str, Any]:
        """Get current ethics state summary."""
        # Calculate average score safely
        if self.session_scores:
            if SCIENTIFIC_LIBRARIES_AVAILABLE and np is not None:
                avg_score = float(np.mean(self.session_scores))
            else:
                avg_score = sum(self.session_scores) / len(self.session_scores)
        else:
            avg_score = 0.5
            
        return {
            "trust_level": self.current_trust_level,
            "unethical_streak": self.unethical_streak,
            "session_prompts": len(self.session_prompts),
            "average_score": avg_score,
            "intervention_needed": self.should_trigger_intervention(),
            "recent_scores": self.session_scores[-5:] if self.session_scores else []
        }

class TaskEthicsManager:
    """Manages ethics for specific task completion contexts."""
    
    def __init__(self, task_id: str, user_id: str, ai_service=None):
        """
        Initialize task ethics manager.
        
        Args:
            task_id: ID of the task being worked on
            user_id: ID of the user
            ai_service: AI service instance
        """
        self.task_id = task_id
        self.user_id = user_id
        self.ai_service = ai_service
        self.ethics_tracker = EthicsTracker(ai_service)
        self.task_history = []
    
    def evaluate_task_prompt(self, prompt: str, task_context: str) -> Dict[str, Any]:
        """
        Evaluate a prompt in the context of a specific task.
        
        Args:
            prompt: User's prompt
            task_context: Context about the current task
            
        Returns:
            Dictionary with evaluation results
        """
        # Get ethical assessment
        ethical_score, reasoning = self.ethics_tracker.assess_ethical_usage(
            prompt, 
            f"Task context: {task_context}"
        )
        
        # Update state
        self.ethics_tracker.update_ethics_state(prompt, ethical_score, task_context)
        
        # Record in task history
        self.task_history.append({
            "prompt": prompt,
            "ethical_score": ethical_score,
            "reasoning": reasoning,
            "timestamp": datetime.now(),
            "context": task_context
        })
        
        # Check for intervention
        intervention_needed = self.ethics_tracker.should_trigger_intervention()
        intervention_message = ""
        if intervention_needed:
            intervention_message = self.ethics_tracker.generate_intervention_message()
        
        return {
            "ethical_score": ethical_score,
            "reasoning": reasoning,
            "intervention_needed": intervention_needed,
            "intervention_message": intervention_message,
            "ethics_summary": self.ethics_tracker.get_ethics_summary()
        }
    
    def get_task_ethics_report(self) -> Dict[str, Any]:
        """Get ethics report for this task session."""
        if not self.task_history:
            return {"task_id": self.task_id, "prompts": 0, "average_score": 0.5}
        
        scores = [h["ethical_score"] for h in self.task_history]
        
        # Calculate average score safely
        if scores:
            if SCIENTIFIC_LIBRARIES_AVAILABLE and np is not None:
                avg_score = float(np.mean(scores))
            else:
                avg_score = sum(scores) / len(scores)
        else:
            avg_score = 0.5
        
        return {
            "task_id": self.task_id,
            "user_id": self.user_id,
            "prompts": len(self.task_history),
            "average_score": avg_score,
            "lowest_score": min(scores) if scores else 0.0,
            "highest_score": max(scores) if scores else 1.0,
            "interventions_triggered": sum(1 for h in self.task_history if h["ethical_score"] < 0.4),
            "recent_trend": scores[-3:] if len(scores) >= 3 else scores,
            "summary": self.ethics_tracker.get_ethics_summary()
        } 