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
            
            # Try multiple search approaches
            search_successful = False
            
            # 1. Try DuckDuckGo search
            duckduckgo_results = self._search_duckduckgo(query)
            if duckduckgo_results:
                results["results"].extend(duckduckgo_results)
                search_successful = True
            
            # 2. Try Wikipedia search as fallback
            if not search_successful or len(results["results"]) < 2:
                wiki_results = self._search_wikipedia_for_claim(query)
                if wiki_results:
                    # Convert Wikipedia results to search result format
                    for wiki_item in wiki_results:
                        results["results"].append({
                            "title": wiki_item["source"],
                            "snippet": wiki_item["text"],
                            "url": wiki_item["url"],
                            "source": "Wikipedia"
                        })
                    search_successful = True
            
            # 3. If still no results, provide AI-generated information
            if not search_successful and self.ai_service:
                ai_info = self._generate_ai_search_response(query)
                results["results"].append(ai_info)
                results["summary"] = f"AI-generated information about '{query}'"
            elif not search_successful:
                # Provide at least some information
                results["results"] = [{
                    "title": f"Search for: {query}",
                    "snippet": f"No external search results available for '{query}'. Please try rephrasing your search or using more specific terms.",
                    "url": "",
                    "source": "System"
                }]
                results["summary"] = f"Search completed but no external results found for '{query}'"
            
            # If AI service is available and we have results, generate a summary
            if self.ai_service and results["results"] and not results["summary"]:
                summary = self._generate_search_summary(query, results["results"])
                results["summary"] = summary
            
            # Format and limit results
            results["results"] = results["results"][:result_count]
            results["sources"] = [r.get("url", "") for r in results["results"] if r.get("url")]
            
            # Ensure we always have a meaningful summary
            if not results["summary"]:
                results["summary"] = f"Found {len(results['results'])} results for '{query}'"
            
            return results
            
        except Exception as e:
            logger.error(f"Error in web search: {e}")
            return {
                "success": True,  # Don't fail completely
                "query": query,
                "search_type": search_type,
                "results": [{
                    "title": "Search Error",
                    "snippet": f"Unable to complete search due to technical issues. Query: '{query}'",
                    "url": "",
                    "source": "System"
                }],
                "summary": f"Search encountered technical difficulties for query: '{query}'",
                "sources": []
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
            
            # Initialize results structure
            results = {
                "success": True,
                "claim": claim,
                "evidence": [],
                "assessment": "Requires verification",
                "confidence": "Medium",
                "sources": [],
                "summary": ""
            }
            
            # Try multiple search approaches
            search_successful = False
            
            # 1. Try DuckDuckGo search
            search_results = self.search_web(claim, result_count=5, search_type="facts")
            if search_results["success"] and search_results.get("results"):
                results["evidence"] = self._analyze_evidence(claim, search_results["results"])
                results["sources"] = search_results["sources"]
                search_successful = True
            
            # 2. Try Wikipedia search as fallback
            if not search_successful:
                wiki_results = self._search_wikipedia_for_claim(claim)
                if wiki_results:
                    results["evidence"] = wiki_results
                    search_successful = True
            
            # 3. If no external results, use AI-based analysis
            if self.ai_service:
                ai_assessment = self._get_ai_fact_check_with_fallback(claim, results["evidence"])
                results.update(ai_assessment)
            else:
                # Provide basic assessment without AI
                results["assessment"] = "Unable to verify - requires manual fact-checking"
                results["confidence"] = "Low"
                results["summary"] = f"Could not find reliable sources to verify the claim: '{claim}'. Please consult authoritative sources manually."
            
            # Ensure we always have a meaningful response
            if not results["summary"]:
                if results["evidence"]:
                    results["summary"] = f"Found {len(results['evidence'])} relevant sources. Assessment: {results['assessment']} (Confidence: {results['confidence']})"
                else:
                    results["summary"] = f"Limited information available for fact-checking. Claim requires verification from authoritative sources."
            
            return results
            
        except Exception as e:
            logger.error(f"Error in fact-checking: {e}")
            return {
                "success": True,  # Don't fail completely
                "claim": claim,
                "assessment": "Error occurred during fact-checking",
                "confidence": "Low",
                "evidence": [],
                "sources": [],
                "summary": f"Unable to complete fact-check due to technical issues. Please verify manually: '{claim}'"
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

    def _search_wikipedia_for_claim(self, claim: str) -> List[Dict[str, str]]:
        """Search Wikipedia for information related to a claim."""
        try:
            # Extract key terms from the claim for Wikipedia search
            key_terms = self._extract_key_terms(claim)
            evidence = []
            
            for term in key_terms[:2]:  # Limit to 2 terms to avoid too many requests
                try:
                    # Search Wikipedia
                    search_url = f"https://en.wikipedia.org/w/api.php"
                    search_params = {
                        'action': 'query',
                        'list': 'search',
                        'srsearch': term,
                        'format': 'json',
                        'srlimit': 2
                    }
                    
                    response = requests.get(search_url, params=search_params, headers=self.headers, timeout=10)
                    response.raise_for_status()
                    search_data = response.json()
                    
                    # Get page summaries
                    for page in search_data.get('query', {}).get('search', []):
                        title = page.get('title', '')
                        page_url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
                        
                        # Get page summary
                        summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '_')}"
                        summary_response = requests.get(summary_url, headers=self.headers, timeout=10)
                        
                        if summary_response.status_code == 200:
                            summary_data = summary_response.json()
                            extract = summary_data.get('extract', '')
                            
                            if extract and len(extract) > 50:
                                evidence.append({
                                    "source": f"Wikipedia - {title}",
                                    "text": extract[:300] + "..." if len(extract) > 300 else extract,
                                    "url": page_url,
                                    "relevance": "Medium"
                                })
                        
                except Exception as e:
                    logger.warning(f"Error searching Wikipedia for term '{term}': {e}")
                    continue
            
            return evidence[:3]  # Limit to 3 pieces of evidence
            
        except Exception as e:
            logger.error(f"Error in Wikipedia search: {e}")
            return []

    def _extract_key_terms(self, claim: str) -> List[str]:
        """Extract key terms from a claim for searching."""
        # Remove common words and extract meaningful terms
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'that', 'this', 'it', 'they', 'them', 'their'}
        
        # Clean and split the claim
        words = re.findall(r'\b[A-Za-z]+\b', claim.lower())
        key_terms = [word for word in words if word not in common_words and len(word) > 2]
        
        # Return top terms (prefer longer/more specific terms)
        key_terms.sort(key=len, reverse=True)
        return key_terms[:5]

    def _generate_ai_search_response(self, query: str) -> Dict[str, str]:
        """Generate AI-based search response when external APIs fail."""
        if not self.ai_service or not hasattr(self.ai_service, 'provider'):
            return {
                "title": f"Information about: {query}",
                "snippet": f"External search sources unavailable. Please research '{query}' using academic databases, official websites, or other reliable sources.",
                "url": "",
                "source": "AI Assistant"
            }
        
        try:
            prompt = f"""Provide helpful information about: "{query}"

Give a brief, factual overview (2-3 sentences) that would be useful for academic research. Include:
- Key concepts or definitions
- Important context or background
- Suggestions for further research

Keep the response objective and educational."""

            response = self.ai_service.provider.generate_content(prompt)
            
            if response and len(response.strip()) > 20:
                return {
                    "title": f"AI Overview: {query}",
                    "snippet": response.strip()[:300] + "..." if len(response) > 300 else response.strip(),
                    "url": "",
                    "source": "AI Assistant"
                }
            else:
                return {
                    "title": f"Information about: {query}",
                    "snippet": f"AI information not available. Please research '{query}' using academic sources.",
                    "url": "",
                    "source": "AI Assistant"
                }
            
        except Exception as e:
            logger.error(f"Error generating AI search response: {e}")
            return {
                "title": f"Information about: {query}",
                "snippet": f"Search assistance unavailable. Please research '{query}' manually using reliable sources.",
                "url": "",
                "source": "System"
            }

    def _get_ai_fact_check_with_fallback(self, claim: str, evidence: List[Dict[str, str]]) -> Dict[str, Any]:
        """Get AI-powered fact-check assessment with fallback logic."""
        if not self.ai_service or not hasattr(self.ai_service, 'provider'):
            return {
                "assessment": "AI analysis not available",
                "confidence": "Low",
                "summary": f"Cannot verify claim automatically. Manual fact-checking recommended for: '{claim}'"
            }
        
        try:
            if evidence:
                evidence_text = "\n".join([f"- {ev['text'][:200]}..." for ev in evidence[:3]])
                prompt = f"""Fact-check this claim based on the provided evidence:

Claim: "{claim}"

Evidence found:
{evidence_text}

Provide a clear fact-check assessment:
1. Assessment (True/False/Partially True/Inconclusive/Requires Further Investigation)
2. Confidence level (High/Medium/Low)
3. Brief explanation (2-3 sentences)

Format your response as:
Assessment: [assessment]
Confidence: [confidence]
Explanation: [explanation]"""
            else:
                prompt = f"""Analyze this claim for fact-checking:

Claim: "{claim}"

No external evidence was found. Based on your knowledge, provide:
1. Assessment (True/False/Partially True/Inconclusive/Requires Further Investigation)
2. Confidence level (High/Medium/Low)  
3. Brief explanation noting the lack of current sources

Format your response as:
Assessment: [assessment]
Confidence: [confidence]
Explanation: [explanation]"""

            response = self.ai_service.provider.generate_content(prompt)
            
            # Parse AI response with better error handling
            assessment = "Requires verification"
            confidence = "Low"
            explanation = "Analysis could not be completed"
            
            if response:
                lines = response.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('Assessment:'):
                        assessment = line.split(':', 1)[1].strip()
                    elif line.startswith('Confidence:'):
                        confidence = line.split(':', 1)[1].strip()
                    elif line.startswith('Explanation:'):
                        explanation = line.split(':', 1)[1].strip()
                
                # If parsing failed, use the whole response as explanation
                if assessment == "Requires verification" and response:
                    explanation = response.strip()
                    assessment = "Analysis provided"
            
            return {
                "assessment": assessment,
                "confidence": confidence,
                "summary": explanation
            }
            
        except Exception as e:
            logger.error(f"Error in AI fact-check: {e}")
            return {
                "assessment": "Technical error occurred",
                "confidence": "Low",
                "summary": f"Could not complete AI analysis. Please manually verify: '{claim}'"
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