"""
Wikipedia and Encyclopedia Lookup for research assistance.

This module provides Wikipedia search and content retrieval functionality
to help students get background information and reliable overviews.
"""

import logging
import requests
import json
from typing import Dict, List, Any, Optional
from urllib.parse import quote_plus
import re

logger = logging.getLogger(__name__)

class WikipediaLookupService:
    """Wikipedia and encyclopedia lookup service."""
    
    def __init__(self, ai_service=None):
        self.ai_service = ai_service
        self.base_url = "https://en.wikipedia.org/api/rest_v1"
        self.api_url = "https://en.wikipedia.org/w/api.php"
        self.headers = {
            'User-Agent': 'ThesisHelper/1.0 (Educational Research Tool)'
        }
    
    def search_wikipedia(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """
        Search Wikipedia for articles related to the query.
        
        Args:
            query: Search term
            limit: Maximum number of results
        
        Returns:
            Dictionary with search results
        """
        try:
            if not query.strip():
                return {
                    "success": False,
                    "error": "No search query provided"
                }
            
            # Search for articles
            search_results = self._search_articles(query, limit)
            
            results = {
                "success": True,
                "query": query,
                "articles": search_results,
                "total_found": len(search_results)
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching Wikipedia: {e}")
            return {
                "success": False,
                "error": f"Wikipedia search failed: {str(e)}"
            }
    
    def get_article_summary(self, title: str, sentences: int = 3) -> Dict[str, Any]:
        """
        Get a summary of a Wikipedia article.
        
        Args:
            title: Article title
            sentences: Number of sentences to include in summary
        
        Returns:
            Dictionary with article summary and metadata
        """
        try:
            if not title.strip():
                return {
                    "success": False,
                    "error": "No article title provided"
                }
            
            # Get page summary
            summary_data = self._get_page_summary(title)
            
            if not summary_data:
                return {
                    "success": False,
                    "error": f"Article '{title}' not found"
                }
            
            # Get additional details if needed
            extract = self._get_page_extract(title, sentences)
            
            results = {
                "success": True,
                "title": summary_data.get("title", title),
                "summary": summary_data.get("extract", ""),
                "detailed_extract": extract,
                "url": summary_data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                "thumbnail": summary_data.get("thumbnail", {}).get("source", "") if summary_data.get("thumbnail") else "",
                "categories": self._get_article_categories(title),
                "key_facts": self._extract_key_facts(summary_data.get("extract", "")),
                "last_modified": summary_data.get("timestamp", "")
            }
            
            # Get AI-generated topic overview if available
            if self.ai_service:
                overview = self._generate_topic_overview(title, results["summary"])
                results["ai_overview"] = overview
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting article summary: {e}")
            return {
                "success": False,
                "error": f"Failed to get article summary: {str(e)}"
            }
    
    def get_topic_overview(self, topic: str) -> Dict[str, Any]:
        """
        Get a comprehensive overview of a topic from multiple Wikipedia sources.
        
        Args:
            topic: Topic to research
        
        Returns:
            Dictionary with comprehensive topic information
        """
        try:
            # First, search for the main article
            search_results = self.search_wikipedia(topic, limit=1)
            
            if not search_results["success"] or not search_results["articles"]:
                return {
                    "success": False,
                    "error": f"No Wikipedia articles found for '{topic}'"
                }
            
            main_article = search_results["articles"][0]
            article_summary = self.get_article_summary(main_article["title"])
            
            if not article_summary["success"]:
                return article_summary
            
            # Search for related articles
            related_search = self.search_wikipedia(f"{topic} related", limit=3)
            related_articles = related_search.get("articles", [])[:3]
            
            # Compile comprehensive overview
            results = {
                "success": True,
                "topic": topic,
                "main_article": article_summary,
                "related_articles": [],
                "key_concepts": [],
                "suggested_reading": []
            }
            
            # Get summaries of related articles
            for article in related_articles:
                if article["title"] != main_article["title"]:
                    related_summary = self.get_article_summary(article["title"], sentences=2)
                    if related_summary["success"]:
                        results["related_articles"].append({
                            "title": related_summary["title"],
                            "summary": related_summary["summary"][:200] + "...",
                            "url": related_summary["url"]
                        })
            
            # Extract key concepts
            if article_summary.get("categories"):
                results["key_concepts"] = article_summary["categories"][:5]
            
            # Generate reading suggestions
            results["suggested_reading"] = self._generate_reading_suggestions(topic, article_summary)
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting topic overview: {e}")
            return {
                "success": False,
                "error": f"Failed to get topic overview: {str(e)}"
            }
    
    def _search_articles(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search for Wikipedia articles."""
        try:
            params = {
                'action': 'query',
                'format': 'json',
                'list': 'search',
                'srsearch': query,
                'srlimit': limit,
                'srprop': 'snippet|titlesnippet|size|timestamp'
            }
            
            response = requests.get(self.api_url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            articles = []
            
            for item in data.get('query', {}).get('search', []):
                # Clean HTML tags from snippet
                snippet = re.sub(r'<[^>]+>', '', item.get('snippet', ''))
                
                articles.append({
                    "title": item.get('title', ''),
                    "snippet": snippet,
                    "size": item.get('size', 0),
                    "timestamp": item.get('timestamp', ''),
                    "url": f"https://en.wikipedia.org/wiki/{quote_plus(item.get('title', ''))}"
                })
            
            return articles
            
        except Exception as e:
            logger.error(f"Error searching articles: {e}")
            return []
    
    def _get_page_summary(self, title: str) -> Optional[Dict[str, Any]]:
        """Get page summary using REST API."""
        try:
            encoded_title = quote_plus(title)
            url = f"{self.base_url}/page/summary/{encoded_title}"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting page summary: {e}")
            return None
    
    def _get_page_extract(self, title: str, sentences: int) -> str:
        """Get page extract with specified number of sentences."""
        try:
            params = {
                'action': 'query',
                'format': 'json',
                'prop': 'extracts',
                'exsentences': sentences,
                'explaintext': True,
                'titles': title
            }
            
            response = requests.get(self.api_url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            pages = data.get('query', {}).get('pages', {})
            
            for page_id, page_data in pages.items():
                if page_id != '-1':  # Page found
                    return page_data.get('extract', '')
            
            return ""
            
        except Exception as e:
            logger.error(f"Error getting page extract: {e}")
            return ""
    
    def _get_article_categories(self, title: str) -> List[str]:
        """Get article categories."""
        try:
            params = {
                'action': 'query',
                'format': 'json',
                'prop': 'categories',
                'titles': title,
                'cllimit': 10
            }
            
            response = requests.get(self.api_url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            pages = data.get('query', {}).get('pages', {})
            
            categories = []
            for page_id, page_data in pages.items():
                if page_id != '-1':
                    for cat in page_data.get('categories', []):
                        cat_title = cat.get('title', '').replace('Category:', '')
                        if not cat_title.startswith(('Articles', 'Pages', 'Wikipedia')):
                            categories.append(cat_title)
            
            return categories[:5]  # Return top 5 relevant categories
            
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []
    
    def _extract_key_facts(self, text: str) -> List[str]:
        """Extract key facts from article text."""
        if not text:
            return []
        
        # Simple fact extraction based on patterns
        facts = []
        
        # Look for dates
        date_pattern = r'\b(?:born|died|founded|established|created|occurred)\s+(?:in\s+)?(\d{4})\b'
        date_matches = re.findall(date_pattern, text, re.IGNORECASE)
        for date in date_matches[:2]:
            facts.append(f"Year: {date}")
        
        # Look for locations
        location_pattern = r'\b(?:in|from|located in|based in)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        location_matches = re.findall(location_pattern, text)
        for location in location_matches[:2]:
            if len(location.split()) <= 3:  # Avoid too long phrases
                facts.append(f"Location: {location}")
        
        # Look for definitions (is/are/was/were statements)
        sentences = text.split('.')
        for sentence in sentences[:3]:
            if any(word in sentence.lower() for word in [' is ', ' are ', ' was ', ' were ']):
                if len(sentence.strip()) < 150:  # Not too long
                    facts.append(sentence.strip())
        
        return facts[:5]  # Return top 5 facts
    
    def _generate_topic_overview(self, title: str, summary: str) -> Dict[str, Any]:
        """Generate AI-powered topic overview."""
        if not self.ai_service or not hasattr(self.ai_service, 'provider'):
            return {"available": False}
        
        try:
            prompt = f"""Provide a brief academic overview of the topic "{title}" based on this Wikipedia summary:

Summary: {summary[:800]}

Please provide:
1. Key points (3-4 bullet points)
2. Why this topic is important for academic research
3. Potential research areas or questions
4. How it relates to broader fields of study

Keep it concise and academic in tone."""

            response = self.ai_service.provider.generate_content(prompt)
            
            return {
                "available": True,
                "overview": response.strip() if response else "Overview not available"
            }
            
        except Exception as e:
            logger.error(f"Error generating topic overview: {e}")
            return {"available": False, "error": str(e)}
    
    def _generate_reading_suggestions(self, topic: str, article_data: Dict[str, Any]) -> List[str]:
        """Generate reading suggestions based on the topic."""
        suggestions = []
        
        # Add the main Wikipedia article
        if article_data.get("url"):
            suggestions.append(f"Wikipedia: {article_data['title']}")
        
        # Suggest related topics based on categories
        categories = article_data.get("categories", [])
        for category in categories[:3]:
            suggestions.append(f"Explore: {category}")
        
        # General academic suggestions
        suggestions.extend([
            f"Academic papers about {topic}",
            f"Books on {topic}",
            f"Recent research in {topic}"
        ])
        
        return suggestions[:5]

# Global instance
_wikipedia_service = None

def create_wikipedia_service(ai_service) -> WikipediaLookupService:
    """Create a Wikipedia lookup service instance."""
    return WikipediaLookupService(ai_service)

def search_wikipedia(query: str, ai_service, limit: int = 5) -> Dict[str, Any]:
    """Search Wikipedia articles."""
    service = WikipediaLookupService(ai_service)
    return service.search_wikipedia(query, limit)

def get_article_summary(title: str, ai_service, sentences: int = 3) -> Dict[str, Any]:
    """Get Wikipedia article summary."""
    service = WikipediaLookupService(ai_service)
    return service.get_article_summary(title, sentences)

def get_topic_overview(topic: str, ai_service) -> Dict[str, Any]:
    """Get comprehensive topic overview."""
    service = WikipediaLookupService(ai_service)
    return service.get_topic_overview(topic) 