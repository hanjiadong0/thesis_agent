"""
Web Search and Fact Checker for research assistance.

This module provides web search capabilities and fact-checking functionality
to help students find current information and verify claims.
"""

import logging
import requests
import json
from typing import Dict, List, Any, Optional
from urllib.parse import quote_plus
import re

logger = logging.getLogger(__name__)

class WebSearchService:
    """Web search and fact-checking service."""
    
    def __init__(self, ai_service=None):
        self.ai_service = ai_service
        # Using DuckDuckGo Instant Answer API (free, no API key required)
        self.search_endpoints = {
            'duckduckgo': 'https://api.duckduckgo.com/',
            'wikipedia': 'https://en.wikipedia.org/api/rest_v1/page/summary/',
        }
        self.headers = {
            'User-Agent': 'ThesisHelper/1.0 (Educational Research Tool)'
        }
    
    def search_web(self, query: str, result_count: int = 5, search_type: str = "general") -> Dict[str, Any]:
        """
        Search the web for information.
        
        Args:
            query: Search query
            result_count: Number of results to return
            search_type: Type of search ("general", "academic", "news", "facts")
        
        Returns:
            Dictionary with search results and metadata
        """
        try:
            if not query.strip():
                return {
                    "success": False,
                    "error": "No search query provided"
                }
            
            results = {
                "success": True,
                "query": query,
                "search_type": search_type,
                "results": [],
                "summary": "",
                "sources": []
            }
            
            # Get search results from multiple sources
            duckduckgo_results = self._search_duckduckgo(query)
            results["results"].extend(duckduckgo_results)
            
            # If AI service is available, generate a summary
            if self.ai_service and results["results"]:
                summary = self._generate_search_summary(query, results["results"])
                results["summary"] = summary
            
            # Format and limit results
            results["results"] = results["results"][:result_count]
            results["sources"] = [r.get("url", "") for r in results["results"] if r.get("url")]
            
            return results
            
        except Exception as e:
            logger.error(f"Error in web search: {e}")
            return {
                "success": False,
                "error": f"Search failed: {str(e)}"
            }
    
    def fact_check(self, claim: str) -> Dict[str, Any]:
        """
        Fact-check a claim by searching for supporting/contradicting evidence.
        
        Args:
            claim: The claim to fact-check
        
        Returns:
            Dictionary with fact-check results
        """
        try:
            if not claim.strip():
                return {
                    "success": False,
                    "error": "No claim provided for fact-checking"
                }
            
            # Search for information about the claim
            search_results = self.search_web(claim, result_count=10, search_type="facts")
            
            if not search_results["success"]:
                return search_results
            
            results = {
                "success": True,
                "claim": claim,
                "evidence": [],
                "assessment": "Unknown",
                "confidence": "Low",
                "sources": search_results["sources"]
            }
            
            # Analyze search results for evidence
            if search_results["results"]:
                results["evidence"] = self._analyze_evidence(claim, search_results["results"])
            
            # Get AI assessment if available
            if self.ai_service:
                ai_assessment = self._get_ai_fact_check(claim, results["evidence"])
                results.update(ai_assessment)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in fact-checking: {e}")
            return {
                "success": False,
                "error": f"Fact-check failed: {str(e)}"
            }
    
    def verify_source(self, url: str) -> Dict[str, Any]:
        """
        Verify the credibility of a source URL.
        
        Args:
            url: URL to verify
        
        Returns:
            Dictionary with source verification results
        """
        try:
            results = {
                "success": True,
                "url": url,
                "domain": "",
                "credibility_score": 0,
                "source_type": "Unknown",
                "warnings": [],
                "recommendations": []
            }
            
            # Extract domain
            domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url)
            if domain_match:
                results["domain"] = domain_match.group(1)
            
            # Assess credibility based on domain
            credibility_info = self._assess_domain_credibility(results["domain"])
            results.update(credibility_info)
            
            return results
            
        except Exception as e:
            logger.error(f"Error verifying source: {e}")
            return {
                "success": False,
                "error": f"Source verification failed: {str(e)}"
            }
    
    def _search_duckduckgo(self, query: str) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo Instant Answer API."""
        try:
            url = self.search_endpoints['duckduckgo']
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            # Parse instant answer
            if data.get('AbstractText'):
                results.append({
                    "title": data.get('Heading', 'Instant Answer'),
                    "snippet": data.get('AbstractText', ''),
                    "url": data.get('AbstractURL', ''),
                    "source": "DuckDuckGo Instant Answer"
                })
            
            # Parse related topics
            for topic in data.get('RelatedTopics', [])[:3]:
                if isinstance(topic, dict) and topic.get('Text'):
                    results.append({
                        "title": topic.get('Text', '').split(' - ')[0],
                        "snippet": topic.get('Text', ''),
                        "url": topic.get('FirstURL', ''),
                        "source": "DuckDuckGo Related"
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return []
    
    def _generate_search_summary(self, query: str, results: List[Dict[str, Any]]) -> str:
        """Generate a summary of search results using AI."""
        if not self.ai_service or not hasattr(self.ai_service, 'provider'):
            return "Summary not available"
        
        try:
            # Prepare content for summarization
            content = f"Query: {query}\n\n"
            for i, result in enumerate(results[:5], 1):
                content += f"{i}. {result.get('title', 'No title')}\n"
                content += f"   {result.get('snippet', 'No description')}\n\n"
            
            prompt = f"""Summarize the following search results about "{query}":

{content}

Provide a concise, informative summary that:
1. Answers the search query
2. Highlights key information
3. Notes any conflicting information
4. Stays objective and factual

Summary:"""

            response = self.ai_service.provider.generate_content(prompt)
            return response.strip() if response else "Summary could not be generated"
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return "Summary generation failed"
    
    def _analyze_evidence(self, claim: str, results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Analyze search results for evidence supporting or contradicting a claim."""
        evidence = []
        
        for result in results:
            snippet = result.get('snippet', '').lower()
            claim_lower = claim.lower()
            
            # Simple keyword matching for evidence analysis
            claim_words = set(claim_lower.split())
            snippet_words = set(snippet.split())
            overlap = len(claim_words.intersection(snippet_words))
            
            if overlap >= 2:  # Significant overlap
                evidence.append({
                    "source": result.get('title', 'Unknown source'),
                    "text": result.get('snippet', ''),
                    "url": result.get('url', ''),
                    "relevance": "High" if overlap >= 3 else "Medium"
                })
        
        return evidence[:5]  # Limit to 5 pieces of evidence
    
    def _get_ai_fact_check(self, claim: str, evidence: List[Dict[str, str]]) -> Dict[str, Any]:
        """Get AI-powered fact-check assessment."""
        if not self.ai_service or not hasattr(self.ai_service, 'provider'):
            return {"assessment": "AI analysis not available"}
        
        try:
            evidence_text = "\n".join([
                f"- {ev['text']}" for ev in evidence[:3]
            ])
            
            prompt = f"""Fact-check this claim based on the provided evidence:

Claim: "{claim}"

Evidence found:
{evidence_text}

Assess the claim and provide:
1. Assessment (True/False/Partially True/Inconclusive)
2. Confidence level (High/Medium/Low)
3. Brief explanation

Format your response as:
Assessment: [assessment]
Confidence: [confidence]
Explanation: [explanation]"""

            response = self.ai_service.provider.generate_content(prompt)
            
            # Parse AI response
            assessment = "Inconclusive"
            confidence = "Low"
            explanation = response.strip() if response else "No analysis available"
            
            if response:
                lines = response.split('\n')
                for line in lines:
                    if line.startswith('Assessment:'):
                        assessment = line.split(':', 1)[1].strip()
                    elif line.startswith('Confidence:'):
                        confidence = line.split(':', 1)[1].strip()
            
            return {
                "assessment": assessment,
                "confidence": confidence,
                "ai_explanation": explanation
            }
            
        except Exception as e:
            logger.error(f"Error in AI fact-check: {e}")
            return {"assessment": "Analysis failed", "confidence": "Low"}
    
    def _assess_domain_credibility(self, domain: str) -> Dict[str, Any]:
        """Assess the credibility of a domain."""
        if not domain:
            return {"credibility_score": 0, "source_type": "Unknown"}
        
        domain_lower = domain.lower()
        
        # High credibility domains
        high_credibility = [
            'wikipedia.org', 'scholar.google.com', 'pubmed.ncbi.nlm.nih.gov',
            'nature.com', 'science.org', 'cell.com', 'nejm.org',
            'gov', 'edu', 'org'  # TLD patterns
        ]
        
        # Medium credibility domains
        medium_credibility = [
            'bbc.com', 'reuters.com', 'ap.org', 'npr.org',
            'scientificamerican.com', 'nationalgeographic.com'
        ]
        
        # Warning signs
        warning_signs = [
            'blog', 'wordpress', 'tumblr', 'facebook', 'twitter',
            'youtube', 'tiktok', 'instagram'
        ]
        
        credibility_score = 3  # Default medium score
        source_type = "General website"
        warnings = []
        recommendations = []
        
        # Check for high credibility
        for pattern in high_credibility:
            if pattern in domain_lower:
                credibility_score = 8
                if pattern in ['gov', 'edu']:
                    source_type = "Government/Academic"
                elif 'wikipedia' in pattern:
                    source_type = "Encyclopedia"
                elif any(x in pattern for x in ['pubmed', 'scholar', 'nature', 'science']):
                    source_type = "Academic/Scientific"
                break
        
        # Check for medium credibility
        if credibility_score == 3:
            for pattern in medium_credibility:
                if pattern in domain_lower:
                    credibility_score = 6
                    source_type = "News/Media"
                    break
        
        # Check for warning signs
        for warning in warning_signs:
            if warning in domain_lower:
                credibility_score = max(1, credibility_score - 2)
                warnings.append(f"May be {warning} content - verify information")
                source_type = "Social media/Blog"
        
        # Add recommendations
        if credibility_score >= 7:
            recommendations.append("Highly reliable source")
        elif credibility_score >= 5:
            recommendations.append("Generally reliable, cross-reference important claims")
        else:
            recommendations.append("Use with caution, verify with additional sources")
        
        return {
            "credibility_score": credibility_score,
            "source_type": source_type,
            "warnings": warnings,
            "recommendations": recommendations
        }

# Global instance
_web_search_service = None

def create_web_search_service(ai_service) -> WebSearchService:
    """Create a web search service instance."""
    return WebSearchService(ai_service)

def search_web(query: str, ai_service, result_count: int = 5, search_type: str = "general") -> Dict[str, Any]:
    """Search the web for information."""
    service = WebSearchService(ai_service)
    return service.search_web(query, result_count, search_type)

def fact_check(claim: str, ai_service) -> Dict[str, Any]:
    """Fact-check a claim."""
    service = WebSearchService(ai_service)
    return service.fact_check(claim)

def verify_source(url: str, ai_service) -> Dict[str, Any]:
    """Verify source credibility."""
    service = WebSearchService(ai_service)
    return service.verify_source(url) 