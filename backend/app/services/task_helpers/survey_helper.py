"""
Survey and Data Collection Helper for research assistance.

This module provides tools to help students design surveys, create questionnaires,
and plan data collection strategies for their thesis research.
"""

import logging
import json
from typing import Dict, List, Any, Optional
import re

logger = logging.getLogger(__name__)

class SurveyDataHelper:
    """Survey and data collection assistance service."""
    
    def __init__(self, ai_service=None):
        self.ai_service = ai_service
        self.question_types = {
            'multiple_choice': 'Multiple Choice',
            'likert_scale': 'Likert Scale (1-5 or 1-7)',
            'yes_no': 'Yes/No',
            'open_ended': 'Open-ended Text',
            'ranking': 'Ranking Order',
            'rating': 'Rating Scale',
            'demographic': 'Demographic Information'
        }
        
        self.survey_templates = {
            'customer_satisfaction': {
                'name': 'Customer Satisfaction Survey',
                'description': 'Measure customer satisfaction and feedback',
                'categories': ['satisfaction', 'usability', 'recommendations']
            },
            'academic_research': {
                'name': 'Academic Research Survey',
                'description': 'General academic research questionnaire',
                'categories': ['demographics', 'research_questions', 'opinions']
            },
            'user_experience': {
                'name': 'User Experience Survey',
                'description': 'Evaluate user experience with products/services',
                'categories': ['usability', 'satisfaction', 'preferences']
            },
            'employee_feedback': {
                'name': 'Employee Feedback Survey',
                'description': 'Collect employee opinions and feedback',
                'categories': ['job_satisfaction', 'workplace_environment', 'suggestions']
            }
        }
    
    def generate_survey_questions(self, research_topic: str, question_count: int = 10, 
                                question_types: List[str] = None) -> Dict[str, Any]:
        """
        Generate survey questions based on research topic.
        
        Args:
            research_topic: The main research topic
            question_count: Number of questions to generate
            question_types: List of desired question types
        
        Returns:
            Dictionary with generated questions and metadata
        """
        try:
            if not research_topic.strip():
                return {
                    "success": False,
                    "error": "No research topic provided"
                }
            
            if question_types is None:
                question_types = ['multiple_choice', 'likert_scale', 'open_ended']
            
            results = {
                "success": True,
                "research_topic": research_topic,
                "total_questions": question_count,
                "questions": [],
                "question_categories": [],
                "survey_structure": {},
                "recommendations": []
            }
            
            # Generate basic question structure
            basic_questions = self._generate_basic_questions(research_topic, question_count, question_types)
            results["questions"] = basic_questions
            
            # Categorize questions
            results["question_categories"] = self._categorize_questions(basic_questions)
            
            # Create survey structure
            results["survey_structure"] = self._create_survey_structure(basic_questions)
            
            # Get AI-powered question suggestions if available
            if self.ai_service:
                ai_suggestions = self._get_ai_question_suggestions(research_topic, question_count)
                results["ai_suggestions"] = ai_suggestions
            
            # Add general recommendations
            results["recommendations"] = self._get_survey_recommendations(research_topic, question_count)
            
            return results
            
        except Exception as e:
            logger.error(f"Error generating survey questions: {e}")
            return {
                "success": False,
                "error": f"Question generation failed: {str(e)}"
            }
    
    def create_data_collection_plan(self, research_objective: str, target_population: str,
                                  sample_size: int = None) -> Dict[str, Any]:
        """
        Create a data collection plan for research.
        
        Args:
            research_objective: Main research objective
            target_population: Description of target population
            sample_size: Desired sample size
        
        Returns:
            Dictionary with data collection plan
        """
        try:
            if not research_objective.strip() or not target_population.strip():
                return {
                    "success": False,
                    "error": "Research objective and target population required"
                }
            
            results = {
                "success": True,
                "research_objective": research_objective,
                "target_population": target_population,
                "recommended_sample_size": sample_size or self._calculate_sample_size(target_population),
                "data_collection_methods": [],
                "sampling_strategy": {},
                "timeline": {},
                "ethical_considerations": [],
                "data_analysis_suggestions": []
            }
            
            # Suggest data collection methods
            results["data_collection_methods"] = self._suggest_collection_methods(research_objective)
            
            # Create sampling strategy
            results["sampling_strategy"] = self._create_sampling_strategy(target_population, sample_size)
            
            # Generate timeline
            results["timeline"] = self._create_collection_timeline(sample_size or 100)
            
            # Add ethical considerations
            results["ethical_considerations"] = self._get_ethical_considerations()
            
            # Suggest analysis methods
            results["data_analysis_suggestions"] = self._suggest_analysis_methods(research_objective)
            
            # Get AI-powered recommendations if available
            if self.ai_service:
                ai_plan = self._get_ai_collection_plan(research_objective, target_population)
                results["ai_recommendations"] = ai_plan
            
            return results
            
        except Exception as e:
            logger.error(f"Error creating data collection plan: {e}")
            return {
                "success": False,
                "error": f"Plan creation failed: {str(e)}"
            }
    
    def validate_survey_design(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate survey design and provide improvement suggestions.
        
        Args:
            questions: List of survey questions to validate
        
        Returns:
            Dictionary with validation results and suggestions
        """
        try:
            if not questions:
                return {
                    "success": False,
                    "error": "No questions provided for validation"
                }
            
            results = {
                "success": True,
                "total_questions": len(questions),
                "validation_score": 0,
                "issues": [],
                "suggestions": [],
                "question_analysis": {},
                "survey_balance": {}
            }
            
            # Analyze question quality
            results["question_analysis"] = self._analyze_question_quality(questions)
            
            # Check survey balance
            results["survey_balance"] = self._analyze_survey_balance(questions)
            
            # Identify issues
            results["issues"] = self._identify_survey_issues(questions)
            
            # Generate suggestions
            results["suggestions"] = self._generate_improvement_suggestions(questions, results["issues"])
            
            # Calculate overall score
            results["validation_score"] = self._calculate_validation_score(results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error validating survey: {e}")
            return {
                "success": False,
                "error": f"Validation failed: {str(e)}"
            }
    
    def _generate_basic_questions(self, topic: str, count: int, types: List[str]) -> List[Dict[str, Any]]:
        """Generate basic survey questions."""
        questions = []
        
        # Demographics questions (always include 1-2)
        demographics = [
            {
                "id": 1,
                "text": "What is your age group?",
                "type": "multiple_choice",
                "options": ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"],
                "category": "demographics",
                "required": True
            },
            {
                "id": 2,
                "text": "What is your educational background?",
                "type": "multiple_choice",
                "options": ["High School", "Bachelor's Degree", "Master's Degree", "PhD", "Other"],
                "category": "demographics",
                "required": False
            }
        ]
        
        questions.extend(demographics[:min(2, count)])
        
        # Topic-specific questions
        remaining_count = count - len(questions)
        topic_questions = self._generate_topic_questions(topic, remaining_count, types)
        questions.extend(topic_questions)
        
        return questions[:count]
    
    def _generate_topic_questions(self, topic: str, count: int, types: List[str]) -> List[Dict[str, Any]]:
        """Generate topic-specific questions."""
        questions = []
        topic_lower = topic.lower()
        
        # Template questions based on common research patterns
        templates = {
            'satisfaction': [
                f"How satisfied are you with {topic}?",
                f"Would you recommend {topic} to others?",
                f"What aspects of {topic} need improvement?"
            ],
            'usage': [
                f"How often do you use/interact with {topic}?",
                f"What is your primary purpose for using {topic}?",
                f"What challenges do you face with {topic}?"
            ],
            'opinion': [
                f"What is your overall opinion about {topic}?",
                f"How important is {topic} to you?",
                f"What changes would you like to see in {topic}?"
            ]
        }
        
        # Select appropriate templates
        if any(word in topic_lower for word in ['satisfaction', 'experience', 'service']):
            selected_templates = templates['satisfaction']
        elif any(word in topic_lower for word in ['use', 'usage', 'application', 'system']):
            selected_templates = templates['usage']
        else:
            selected_templates = templates['opinion']
        
        # Create questions from templates
        for i, template in enumerate(selected_templates[:count]):
            q_type = types[i % len(types)]
            question = {
                "id": len(questions) + 3,
                "text": template,
                "type": q_type,
                "category": "main_research",
                "required": True
            }
            
            # Add options for multiple choice questions
            if q_type == 'multiple_choice':
                if 'satisfied' in template.lower():
                    question["options"] = ["Very Satisfied", "Satisfied", "Neutral", "Dissatisfied", "Very Dissatisfied"]
                elif 'often' in template.lower():
                    question["options"] = ["Daily", "Weekly", "Monthly", "Rarely", "Never"]
                elif 'recommend' in template.lower():
                    question["options"] = ["Definitely", "Probably", "Maybe", "Probably Not", "Definitely Not"]
                else:
                    question["options"] = ["Excellent", "Good", "Average", "Poor", "Very Poor"]
            
            # Add scale for Likert questions
            elif q_type == 'likert_scale':
                question["scale"] = {
                    "min": 1,
                    "max": 5,
                    "min_label": "Strongly Disagree",
                    "max_label": "Strongly Agree"
                }
            
            questions.append(question)
        
        return questions
    
    def _categorize_questions(self, questions: List[Dict[str, Any]]) -> List[str]:
        """Categorize questions by type."""
        categories = set()
        for question in questions:
            categories.add(question.get("category", "general"))
        return list(categories)
    
    def _create_survey_structure(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create survey structure organization."""
        structure = {
            "sections": [],
            "estimated_time": self._estimate_completion_time(questions),
            "question_flow": "linear"
        }
        
        # Group questions by category
        categories = {}
        for question in questions:
            category = question.get("category", "general")
            if category not in categories:
                categories[category] = []
            categories[category].append(question["id"])
        
        # Create sections
        section_order = ["demographics", "main_research", "general"]
        for category in section_order:
            if category in categories:
                structure["sections"].append({
                    "name": category.replace("_", " ").title(),
                    "questions": categories[category],
                    "description": f"Questions related to {category.replace('_', ' ')}"
                })
        
        return structure
    
    def _estimate_completion_time(self, questions: List[Dict[str, Any]]) -> int:
        """Estimate survey completion time in minutes."""
        time_per_question = {
            'multiple_choice': 0.5,
            'yes_no': 0.3,
            'likert_scale': 0.5,
            'rating': 0.5,
            'ranking': 1.0,
            'open_ended': 2.0,
            'demographic': 0.3
        }
        
        total_time = 0
        for question in questions:
            q_type = question.get("type", "multiple_choice")
            total_time += time_per_question.get(q_type, 1.0)
        
        return max(1, round(total_time))
    
    def _get_ai_question_suggestions(self, topic: str, count: int) -> Dict[str, Any]:
        """Get AI-powered question suggestions."""
        if not self.ai_service or not hasattr(self.ai_service, 'provider'):
            return {"available": False}
        
        try:
            prompt = f"""Generate {count} high-quality survey questions for research on "{topic}".

Please provide:
1. Mix of question types (multiple choice, Likert scale, open-ended)
2. Clear, unbiased wording
3. Relevant to academic research
4. Include both demographic and topic-specific questions

Format each question as:
Type: [question_type]
Question: [question_text]
Options: [if applicable]

Topic: {topic}"""

            response = self.ai_service.provider.generate_content(prompt)
            
            return {
                "available": True,
                "suggestions": response.strip() if response else "No suggestions available"
            }
            
        except Exception as e:
            logger.error(f"Error getting AI suggestions: {e}")
            return {"available": False, "error": str(e)}
    
    def _get_survey_recommendations(self, topic: str, count: int) -> List[str]:
        """Get general survey recommendations."""
        recommendations = [
            f"Keep survey focused on {topic} to maintain respondent engagement",
            f"With {count} questions, estimated completion time is {self._estimate_completion_time([{'type': 'multiple_choice'}] * count)} minutes",
            "Include a mix of question types for comprehensive data",
            "Pre-test your survey with a small group before full deployment",
            "Ensure questions are clear and unbiased",
            "Consider offering incentives for completion",
            "Plan for non-response bias in your analysis"
        ]
        
        if count > 15:
            recommendations.append("Consider reducing question count to improve response rates")
        
        return recommendations
    
    def _suggest_collection_methods(self, objective: str) -> List[Dict[str, str]]:
        """Suggest appropriate data collection methods."""
        objective_lower = objective.lower()
        
        methods = []
        
        # Online surveys
        methods.append({
            "method": "Online Survey",
            "description": "Web-based questionnaire using platforms like Google Forms, SurveyMonkey",
            "pros": "Cost-effective, wide reach, easy data collection",
            "cons": "Potential sampling bias, lower response rates"
        })
        
        # Interviews
        if any(word in objective_lower for word in ['experience', 'opinion', 'perspective', 'qualitative']):
            methods.append({
                "method": "Semi-structured Interviews",
                "description": "In-depth interviews with open-ended questions",
                "pros": "Rich qualitative data, flexibility to explore topics",
                "cons": "Time-consuming, difficult to analyze, small sample sizes"
            })
        
        # Focus groups
        if any(word in objective_lower for word in ['group', 'discussion', 'feedback']):
            methods.append({
                "method": "Focus Groups",
                "description": "Facilitated group discussions",
                "pros": "Group dynamics, multiple perspectives, cost-effective",
                "cons": "Potential groupthink, difficult to schedule"
            })
        
        # Observations
        if any(word in objective_lower for word in ['behavior', 'usage', 'interaction']):
            methods.append({
                "method": "Observational Study",
                "description": "Direct observation of behaviors or phenomena",
                "pros": "Natural behavior, no self-report bias",
                "cons": "Time-intensive, observer bias, limited scope"
            })
        
        return methods
    
    def _create_sampling_strategy(self, population: str, sample_size: Optional[int]) -> Dict[str, Any]:
        """Create sampling strategy recommendations."""
        return {
            "target_population": population,
            "recommended_sampling_methods": [
                "Random sampling (if population list available)",
                "Stratified sampling (for diverse populations)",
                "Convenience sampling (for pilot studies)",
                "Snowball sampling (for hard-to-reach groups)"
            ],
            "sample_size_calculation": {
                "recommended_minimum": sample_size or 100,
                "confidence_level": "95%",
                "margin_of_error": "5%",
                "note": "Larger samples provide more reliable results"
            },
            "recruitment_strategies": [
                "Social media outreach",
                "Email invitations",
                "Partner organizations",
                "Academic networks",
                "Incentive programs"
            ]
        }
    
    def _calculate_sample_size(self, population: str) -> int:
        """Calculate recommended sample size."""
        # Simple heuristic based on population description
        population_lower = population.lower()
        
        if any(word in population_lower for word in ['student', 'university', 'college']):
            return 200  # University populations
        elif any(word in population_lower for word in ['employee', 'worker', 'organization']):
            return 150  # Organizational studies
        elif any(word in population_lower for word in ['customer', 'user', 'consumer']):
            return 300  # Consumer research
        else:
            return 100  # General minimum
    
    def _create_collection_timeline(self, sample_size: int) -> Dict[str, str]:
        """Create data collection timeline."""
        # Estimate timeline based on sample size
        if sample_size <= 50:
            duration = "2-3 weeks"
        elif sample_size <= 100:
            duration = "3-4 weeks"
        elif sample_size <= 200:
            duration = "4-6 weeks"
        else:
            duration = "6-8 weeks"
        
        return {
            "preparation": "1 week (survey design, pre-testing)",
            "data_collection": duration,
            "follow_up": "1 week (reminders, final collection)",
            "data_cleaning": "1 week",
            "total_estimated": f"{duration.split('-')[1].strip()} + 3 weeks"
        }
    
    def _get_ethical_considerations(self) -> List[str]:
        """Get ethical considerations for data collection."""
        return [
            "Obtain informed consent from all participants",
            "Ensure participant anonymity and confidentiality",
            "Provide clear information about data usage",
            "Allow participants to withdraw at any time",
            "Secure data storage and transmission",
            "Consider IRB/ethics committee approval if required",
            "Minimize participant burden and risk",
            "Provide contact information for questions",
            "Consider cultural sensitivity in questions",
            "Plan for data retention and disposal"
        ]
    
    def _suggest_analysis_methods(self, objective: str) -> List[str]:
        """Suggest data analysis methods."""
        objective_lower = objective.lower()
        
        methods = [
            "Descriptive statistics (frequencies, means, percentages)",
            "Cross-tabulation analysis for relationships between variables"
        ]
        
        if any(word in objective_lower for word in ['compare', 'difference', 'between']):
            methods.append("T-tests or ANOVA for group comparisons")
        
        if any(word in objective_lower for word in ['relationship', 'correlation', 'association']):
            methods.append("Correlation analysis for variable relationships")
        
        if any(word in objective_lower for word in ['predict', 'influence', 'factor']):
            methods.append("Regression analysis for predictive modeling")
        
        if any(word in objective_lower for word in ['qualitative', 'text', 'open']):
            methods.append("Thematic analysis for open-ended responses")
        
        methods.extend([
            "Data visualization (charts, graphs)",
            "Statistical significance testing",
            "Confidence intervals for estimates"
        ])
        
        return methods
    
    def _get_ai_collection_plan(self, objective: str, population: str) -> Dict[str, Any]:
        """Get AI-powered data collection plan."""
        if not self.ai_service or not hasattr(self.ai_service, 'provider'):
            return {"available": False}
        
        try:
            prompt = f"""Create a comprehensive data collection plan for this research:

Objective: {objective}
Target Population: {population}

Please provide:
1. Most appropriate data collection method
2. Sampling strategy recommendations
3. Key considerations for this specific research
4. Potential challenges and solutions
5. Timeline recommendations

Keep it practical and academically sound."""

            response = self.ai_service.provider.generate_content(prompt)
            
            return {
                "available": True,
                "plan": response.strip() if response else "Plan not available"
            }
            
        except Exception as e:
            logger.error(f"Error getting AI collection plan: {e}")
            return {"available": False, "error": str(e)}
    
    def _analyze_question_quality(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the quality of survey questions."""
        analysis = {
            "total_questions": len(questions),
            "question_types": {},
            "average_complexity": 0,
            "bias_indicators": []
        }
        
        # Count question types
        for question in questions:
            q_type = question.get("type", "unknown")
            analysis["question_types"][q_type] = analysis["question_types"].get(q_type, 0) + 1
        
        # Check for bias indicators
        bias_words = ["should", "don't you think", "obviously", "clearly", "everyone knows"]
        for question in questions:
            text = question.get("text", "").lower()
            for bias_word in bias_words:
                if bias_word in text:
                    analysis["bias_indicators"].append(f"Question {question.get('id', '?')}: Contains '{bias_word}'")
        
        return analysis
    
    def _analyze_survey_balance(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze survey balance and structure."""
        balance = {
            "demographic_questions": 0,
            "research_questions": 0,
            "open_ended_ratio": 0,
            "required_questions": 0
        }
        
        for question in questions:
            if question.get("category") == "demographics":
                balance["demographic_questions"] += 1
            else:
                balance["research_questions"] += 1
            
            if question.get("type") == "open_ended":
                balance["open_ended_ratio"] += 1
            
            if question.get("required", False):
                balance["required_questions"] += 1
        
        balance["open_ended_ratio"] = balance["open_ended_ratio"] / len(questions) if questions else 0
        
        return balance
    
    def _identify_survey_issues(self, questions: List[Dict[str, Any]]) -> List[str]:
        """Identify potential issues with the survey."""
        issues = []
        
        if len(questions) > 20:
            issues.append("Survey may be too long - consider reducing questions")
        
        open_ended_count = sum(1 for q in questions if q.get("type") == "open_ended")
        if open_ended_count > len(questions) * 0.3:
            issues.append("Too many open-ended questions may reduce response rate")
        
        required_count = sum(1 for q in questions if q.get("required", False))
        if required_count > len(questions) * 0.8:
            issues.append("Too many required questions may frustrate respondents")
        
        # Check for demographic balance
        demo_count = sum(1 for q in questions if q.get("category") == "demographics")
        if demo_count > 5:
            issues.append("Too many demographic questions")
        elif demo_count == 0:
            issues.append("No demographic questions - consider adding basic demographics")
        
        return issues
    
    def _generate_improvement_suggestions(self, questions: List[Dict[str, Any]], issues: List[str]) -> List[str]:
        """Generate suggestions for improving the survey."""
        suggestions = []
        
        if "too long" in str(issues).lower():
            suggestions.append("Prioritize most important questions and remove redundant ones")
        
        if "open-ended" in str(issues).lower():
            suggestions.append("Convert some open-ended questions to multiple choice for easier analysis")
        
        if "required" in str(issues).lower():
            suggestions.append("Make only essential questions required to improve completion rates")
        
        suggestions.extend([
            "Add progress indicators to show survey completion status",
            "Include clear instructions for each section",
            "Pre-test survey with small group before full deployment",
            "Consider mobile-friendly design for better accessibility",
            "Add 'Other' options where appropriate for comprehensive responses"
        ])
        
        return suggestions
    
    def _calculate_validation_score(self, results: Dict[str, Any]) -> int:
        """Calculate overall validation score (0-100)."""
        score = 100
        
        # Deduct points for issues
        issues = results.get("issues", [])
        score -= len(issues) * 10
        
        # Check balance
        balance = results.get("survey_balance", {})
        if balance.get("demographic_questions", 0) == 0:
            score -= 15
        
        if balance.get("open_ended_ratio", 0) > 0.4:
            score -= 10
        
        # Question type diversity
        analysis = results.get("question_analysis", {})
        type_count = len(analysis.get("question_types", {}))
        if type_count < 2:
            score -= 10
        
        return max(0, min(100, score))

# Global instance
_survey_helper = None

def create_survey_helper(ai_service) -> SurveyDataHelper:
    """Create a survey helper instance."""
    return SurveyDataHelper(ai_service)

def generate_survey_questions(research_topic: str, ai_service, question_count: int = 10, 
                            question_types: List[str] = None) -> Dict[str, Any]:
    """Generate survey questions."""
    helper = SurveyDataHelper(ai_service)
    return helper.generate_survey_questions(research_topic, question_count, question_types)

def create_data_collection_plan(research_objective: str, target_population: str, ai_service,
                              sample_size: int = None) -> Dict[str, Any]:
    """Create data collection plan."""
    helper = SurveyDataHelper(ai_service)
    return helper.create_data_collection_plan(research_objective, target_population, sample_size) 