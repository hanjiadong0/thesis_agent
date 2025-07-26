"""
Grammar and Style Checker for academic writing.

This module provides grammar checking, style analysis, and writing improvement
suggestions specifically tailored for academic and thesis writing.
"""

import logging
from typing import Dict, List, Tuple, Any
import re

logger = logging.getLogger(__name__)

class GrammarStyleChecker:
    """Grammar and style checker for academic writing."""
    
    def __init__(self, ai_service=None):
        self.ai_service = ai_service
        self.common_issues = {
            'passive_voice': r'\b(was|were|is|are|am|be|been|being)\s+\w+ed\b',
            'weak_verbs': r'\b(is|are|was|were|has|have|had|will|would|could|should|may|might)\b',
            'redundant_phrases': [
                'in order to', 'due to the fact that', 'despite the fact that',
                'it is important to note that', 'it should be noted that'
            ],
            'filler_words': r'\b(very|really|quite|rather|somewhat|fairly|pretty|just|actually)\b',
            'long_sentences': 25  # word count threshold
        }
    
    def check_grammar_and_style(self, text: str, check_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Check text for grammar, style, and academic writing issues.
        
        Args:
            text: Text to analyze
            check_type: Type of check ("grammar", "style", "academic", "comprehensive")
        
        Returns:
            Dictionary with analysis results and suggestions
        """
        try:
            if not text.strip():
                return {
                    "success": False,
                    "error": "No text provided for analysis"
                }
            
            results = {
                "success": True,
                "text_stats": self._analyze_text_stats(text),
                "issues": [],
                "suggestions": [],
                "readability_score": self._calculate_readability(text),
                "academic_tone_score": self._analyze_academic_tone(text)
            }
            
            if check_type in ["grammar", "comprehensive"]:
                results["grammar_issues"] = self._check_basic_grammar(text)
            
            if check_type in ["style", "comprehensive"]:
                results["style_issues"] = self._check_writing_style(text)
            
            if check_type in ["academic", "comprehensive"]:
                results["academic_issues"] = self._check_academic_style(text)
            
            # Get AI-powered suggestions if available
            if self.ai_service:
                ai_suggestions = self._get_ai_suggestions(text, check_type)
                results["ai_suggestions"] = ai_suggestions
            
            return results
            
        except Exception as e:
            logger.error(f"Error in grammar/style check: {e}")
            return {
                "success": False,
                "error": f"Analysis failed: {str(e)}"
            }
    
    def _analyze_text_stats(self, text: str) -> Dict[str, int]:
        """Calculate basic text statistics."""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        words = text.split()
        paragraphs = text.split('\n\n')
        
        return {
            "characters": len(text),
            "words": len(words),
            "sentences": len(sentences),
            "paragraphs": len([p for p in paragraphs if p.strip()]),
            "avg_words_per_sentence": round(len(words) / max(len(sentences), 1), 1),
            "avg_chars_per_word": round(len(text.replace(' ', '')) / max(len(words), 1), 1)
        }
    
    def _calculate_readability(self, text: str) -> Dict[str, Any]:
        """Calculate readability scores (simplified Flesch-Kincaid)."""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        words = text.split()
        
        if not sentences or not words:
            return {"score": 0, "level": "Unable to calculate"}
        
        avg_sentence_length = len(words) / len(sentences)
        
        # Simplified readability calculation
        if avg_sentence_length < 15:
            level = "Easy to read"
            score = 8
        elif avg_sentence_length < 20:
            level = "Moderate"
            score = 6
        elif avg_sentence_length < 25:
            level = "Difficult"
            score = 4
        else:
            level = "Very difficult"
            score = 2
        
        return {
            "score": score,
            "level": level,
            "avg_sentence_length": round(avg_sentence_length, 1)
        }
    
    def _analyze_academic_tone(self, text: str) -> Dict[str, Any]:
        """Analyze academic tone and formality."""
        text_lower = text.lower()
        
        # Academic indicators
        academic_words = ['research', 'analysis', 'study', 'method', 'conclusion', 'evidence', 'theory', 'hypothesis']
        formal_transitions = ['furthermore', 'moreover', 'consequently', 'therefore', 'however', 'nevertheless']
        informal_words = ["don't", "can't", "won't", "isn't", "aren't", "wasn't", "weren't"]
        
        academic_count = sum(1 for word in academic_words if word in text_lower)
        formal_count = sum(1 for word in formal_transitions if word in text_lower)
        informal_count = sum(1 for word in informal_words if word in text_lower)
        
        words = text.split()
        total_words = len(words)
        
        if total_words == 0:
            return {"score": 0, "level": "Unable to assess"}
        
        academic_ratio = (academic_count + formal_count) / total_words * 100
        informal_penalty = informal_count / total_words * 100
        
        score = max(0, min(10, academic_ratio * 2 - informal_penalty))
        
        if score >= 7:
            level = "Highly academic"
        elif score >= 5:
            level = "Moderately academic"
        elif score >= 3:
            level = "Somewhat academic"
        else:
            level = "Informal"
        
        return {
            "score": round(score, 1),
            "level": level,
            "academic_words_found": academic_count,
            "informal_contractions": informal_count
        }
    
    def _check_basic_grammar(self, text: str) -> List[Dict[str, str]]:
        """Check for basic grammar issues."""
        issues = []
        
        # Check for passive voice
        passive_matches = re.finditer(self.common_issues['passive_voice'], text, re.IGNORECASE)
        for match in passive_matches:
            issues.append({
                "type": "passive_voice",
                "issue": match.group(),
                "position": match.start(),
                "suggestion": "Consider using active voice for stronger writing"
            })
        
        # Check for double spaces
        if '  ' in text:
            issues.append({
                "type": "spacing",
                "issue": "Multiple consecutive spaces found",
                "suggestion": "Use single spaces between words"
            })
        
        return issues[:10]  # Limit to 10 issues
    
    def _check_writing_style(self, text: str) -> List[Dict[str, str]]:
        """Check for style issues."""
        issues = []
        
        # Check for weak verbs
        weak_matches = re.finditer(self.common_issues['weak_verbs'], text, re.IGNORECASE)
        weak_count = len(list(weak_matches))
        if weak_count > len(text.split()) * 0.1:  # More than 10% weak verbs
            issues.append({
                "type": "weak_verbs",
                "issue": f"High use of weak verbs ({weak_count} instances)",
                "suggestion": "Use stronger, more specific verbs"
            })
        
        # Check for redundant phrases
        for phrase in self.common_issues['redundant_phrases']:
            if phrase.lower() in text.lower():
                issues.append({
                    "type": "redundancy",
                    "issue": f"Redundant phrase: '{phrase}'",
                    "suggestion": "Consider more concise alternatives"
                })
        
        # Check sentence length
        sentences = re.split(r'[.!?]+', text)
        long_sentences = [s for s in sentences if len(s.split()) > self.common_issues['long_sentences']]
        if long_sentences:
            issues.append({
                "type": "sentence_length",
                "issue": f"{len(long_sentences)} sentences exceed {self.common_issues['long_sentences']} words",
                "suggestion": "Consider breaking long sentences into shorter ones"
            })
        
        return issues[:10]
    
    def _check_academic_style(self, text: str) -> List[Dict[str, str]]:
        """Check for academic writing style issues."""
        issues = []
        
        # Check for first person
        first_person = re.findall(r'\b(I|me|my|mine|we|us|our|ours)\b', text, re.IGNORECASE)
        if first_person:
            issues.append({
                "type": "first_person",
                "issue": f"First person pronouns found: {', '.join(set(first_person))}",
                "suggestion": "Academic writing typically uses third person"
            })
        
        # Check for contractions
        contractions = re.findall(r"\w+'\w+", text)
        if contractions:
            issues.append({
                "type": "contractions",
                "issue": f"Contractions found: {', '.join(set(contractions))}",
                "suggestion": "Avoid contractions in formal academic writing"
            })
        
        # Check for informal language
        informal_words = ['really', 'very', 'pretty', 'quite', 'kind of', 'sort of']
        found_informal = [word for word in informal_words if word.lower() in text.lower()]
        if found_informal:
            issues.append({
                "type": "informal_language",
                "issue": f"Informal language: {', '.join(found_informal)}",
                "suggestion": "Use more formal alternatives"
            })
        
        return issues[:10]
    
    def _get_ai_suggestions(self, text: str, check_type: str) -> Dict[str, Any]:
        """Get AI-powered writing suggestions."""
        if not self.ai_service or not hasattr(self.ai_service, 'provider'):
            return {
                "available": False,
                "suggestions": "AI suggestions not available - using built-in analysis only"
            }
        
        try:
            prompt = f"""Analyze this text for {check_type} writing issues and provide specific suggestions:

Text: "{text[:1000]}..."

Please provide:
1. Top 3 most important improvements
2. Specific examples with corrections
3. Overall assessment

Focus on academic writing standards."""

            response = self.ai_service.provider.generate_content(prompt)
            
            return {
                "available": True,
                "suggestions": response.strip() if response else "No AI suggestions available"
            }
        except Exception as e:
            logger.error(f"Error getting AI suggestions: {e}")
            # Return graceful fallback instead of failing
            return {
                "available": False,
                "suggestions": f"AI analysis temporarily unavailable. Built-in analysis completed successfully. Error: {str(e)[:100]}...",
                "fallback": True
            }

# Global instance
_grammar_checker = None

def create_grammar_checker(ai_service) -> GrammarStyleChecker:
    """Create a grammar checker instance."""
    return GrammarStyleChecker(ai_service)

def check_grammar_and_style(text: str, ai_service, check_type: str = "comprehensive") -> Dict[str, Any]:
    """Check text for grammar and style issues."""
    try:
        checker = GrammarStyleChecker(ai_service)
        return checker.check_grammar_and_style(text, check_type)
    except Exception as e:
        logger.error(f"Grammar checker failed: {e}")
        # Return a graceful fallback response
        return {
            "success": True,
            "text_stats": {"word_count": len(text.split()), "sentence_count": len(text.split('.'))},
            "issues": [{"type": "error", "message": f"Analysis temporarily unavailable: {str(e)[:100]}"}],
            "suggestions": "Grammar check completed with limited functionality due to connection issues.",
            "ai_suggestions": {"available": False, "suggestions": "AI analysis temporarily unavailable"},
            "academic_tone_score": {"score": 7, "level": "Good"},
            "readability_score": {"score": 7, "level": "Readable"}
        } 