#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
semantic_scholar.py
~~~~~~~~~~~~~~~~~~~
Light-weight wrapper around the Semantic Scholar Graph API to fetch
metadata for academic papers.
Adapted for the thesis helper system.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Dict, Any, Optional, List

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None

logger = logging.getLogger(__name__)

class SemanticScholarAPI:
    """Semantic Scholar API client for academic paper metadata."""
    
    def __init__(self):
        self.base_url = "https://api.semanticscholar.org/graph/v1/paper/search"
        self.detail_url = "https://api.semanticscholar.org/graph/v1/paper"
        
        # Get API key from environment if available (for higher rate limits)
        self.api_key = os.getenv("S2_API_KEY")
        self.headers = {}
        if self.api_key:
            self.headers["x-api-key"] = self.api_key
            logger.info("Using Semantic Scholar API key")
    
    def get_paper_metadata(self, query: str) -> Dict[str, Any]:
        """
        Query Semantic Scholar for a single paper and return its metadata.
        
        Args:
            query: Paper title, DOI, or arXiv identifier
            
        Returns:
            Dictionary with paper metadata or empty dict if not found
        """
        if not REQUESTS_AVAILABLE:
            logger.error("requests library not available")
            return {}
        
        if not query or not query.strip():
            logger.error("Empty query provided")
            return {}
        
        try:
            params = {
                "query": query.strip(),
                "limit": 1,
                "fields": (
                    "title,authors,year,venue,abstract,externalIds,"
                    "url,citationCount,publicationDate,referenceCount,influentialCitationCount"
                ),
            }
            
            response = requests.get(
                self.base_url, 
                params=params, 
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get("data"):
                paper = data["data"][0]
                
                # Enrich with additional processing
                processed_paper = self._process_paper_data(paper)
                logger.info(f"Found paper: {processed_paper.get('title', 'Unknown')}")
                return processed_paper
            else:
                logger.warning(f"No papers found for query: {query}")
                return {}
                
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            return {}
        except (KeyError, ValueError) as e:
            logger.error(f"Failed to parse API response: {e}")
            return {}
    
    def get_paper_by_id(self, paper_id: str) -> Dict[str, Any]:
        """
        Get detailed paper information by Semantic Scholar paper ID.
        
        Args:
            paper_id: Semantic Scholar paper ID
            
        Returns:
            Dictionary with paper metadata
        """
        if not REQUESTS_AVAILABLE:
            return {}
        
        try:
            url = f"{self.detail_url}/{paper_id}"
            params = {
                "fields": (
                    "title,authors,year,venue,abstract,externalIds,url,"
                    "citationCount,publicationDate,referenceCount,influentialCitationCount,"
                    "fieldsOfStudy,publicationTypes,publicationVenue"
                )
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            paper = response.json()
            return self._process_paper_data(paper)
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch paper by ID {paper_id}: {e}")
            return {}
    
    def search_papers(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for multiple papers and return results.
        
        Args:
            query: Search query
            limit: Maximum number of results (default: 10, max: 100)
            
        Returns:
            List of paper dictionaries
        """
        if not REQUESTS_AVAILABLE:
            return []
        
        try:
            params = {
                "query": query.strip(),
                "limit": min(limit, 100),  # API limit
                "fields": "title,authors,year,venue,abstract,externalIds,url,citationCount"
            }
            
            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=15
            )
            response.raise_for_status()
            
            data = response.json()
            papers = data.get("data", [])
            
            return [self._process_paper_data(paper) for paper in papers]
            
        except requests.RequestException as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def _process_paper_data(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """Process and standardize paper data from API response."""
        processed = {
            "paperId": paper.get("paperId", ""),
            "title": paper.get("title", "Unknown Title"),
            "year": paper.get("year"),
            "venue": paper.get("venue", ""),
            "abstract": paper.get("abstract", ""),
            "url": paper.get("url", ""),
            "citationCount": paper.get("citationCount", 0),
            "referenceCount": paper.get("referenceCount", 0),
            "influentialCitationCount": paper.get("influentialCitationCount", 0),
            "publicationDate": paper.get("publicationDate", ""),
            "externalIds": paper.get("externalIds", {}),
            "fieldsOfStudy": paper.get("fieldsOfStudy", []),
            "publicationTypes": paper.get("publicationTypes", [])
        }
        
        # Process authors
        authors = paper.get("authors", [])
        processed["authors"] = []
        processed["authorNames"] = []
        
        for author in authors:
            if isinstance(author, dict):
                author_info = {
                    "authorId": author.get("authorId", ""),
                    "name": author.get("name", "Unknown Author")
                }
                processed["authors"].append(author_info)
                processed["authorNames"].append(author_info["name"])
            elif isinstance(author, str):
                processed["authorNames"].append(author)
        
        # Create a readable citation string
        author_str = ", ".join(processed["authorNames"][:3])  # First 3 authors
        if len(processed["authorNames"]) > 3:
            author_str += " et al."
        
        year_str = f" ({processed['year']})" if processed["year"] else ""
        venue_str = f" {processed['venue']}" if processed["venue"] else ""
        
        processed["shortCitation"] = f"{author_str}{year_str}.{venue_str}"
        
        return processed

# Global instance
_api = SemanticScholarAPI()

def get_paper_metadata(query: str) -> Dict[str, Any]:
    """
    Get paper metadata from Semantic Scholar.
    
    Args:
        query: Paper title, DOI, or arXiv identifier
        
    Returns:
        Dictionary with paper metadata
    """
    return _api.get_paper_metadata(query)

def search_papers(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search for papers on Semantic Scholar.
    
    Args:
        query: Search query
        limit: Maximum number of results
        
    Returns:
        List of paper dictionaries
    """
    return _api.search_papers(query, limit) 