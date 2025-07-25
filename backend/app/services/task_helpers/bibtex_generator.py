#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bibtex_generator.py
~~~~~~~~~~~~~~~~~~~
Generate a BibTeX entry from either a DOI or an arXiv ID.
Adapted for the thesis helper system with proper error handling.
"""

from __future__ import annotations

import re
import logging
from datetime import datetime
from typing import Optional, Dict, Any

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None

logger = logging.getLogger(__name__)

class BibTexGenerator:
    """BibTeX citation generator for academic papers."""
    
    def __init__(self):
        self.crossref_url = "https://api.crossref.org/works/"
        self.arxiv_url = "https://export.arxiv.org/api/query?id_list="
        
        # Compiled regex patterns for arXiv parsing
        self.arxiv_title_pattern = re.compile(r"<title>(.*?)</title>", re.S)
        self.arxiv_name_pattern = re.compile(r"<name>(.*?)</name>")
        self.arxiv_published_pattern = re.compile(r"<published>(.*?)</published>")
    
    def _get_crossref_bibtex(self, doi: str) -> str:
        """Generate BibTeX from CrossRef API for DOI."""
        if not REQUESTS_AVAILABLE:
            raise Exception("requests library not available")
            
        try:
            response = requests.get(f"{self.crossref_url}{doi}", timeout=10)
            response.raise_for_status()
            data = response.json()["message"]
            
            # Extract authors safely
            authors = []
            if "author" in data:
                for author in data["author"]:
                    if "family" in author and "given" in author:
                        authors.append(f"{author['family']}, {author['given']}")
                    elif "name" in author:
                        authors.append(author["name"])
            
            author_str = " and ".join(authors) if authors else "Unknown Author"
            
            # Extract publication year
            year = "Unknown"
            if "issued" in data and "date-parts" in data["issued"]:
                try:
                    year = str(data["issued"]["date-parts"][0][0])
                except (IndexError, TypeError):
                    pass
            
            # Extract title and journal
            title = data.get("title", ["Unknown Title"])[0]
            journal = data.get("container-title", ["Unknown Journal"])[0]
            
            return (
                f"@article{{{data.get('DOI', doi)}}},\n"
                f"  title   = {{ {title} }},\n"
                f"  author  = {{ {author_str} }},\n"
                f"  journal = {{ {journal} }},\n"
                f"  year    = {{ {year} }},\n"
                f"  doi     = {{ {data.get('DOI', doi)} }}\n"
                f"}}"
            )
            
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch DOI data: {e}")
        except (KeyError, ValueError) as e:
            raise Exception(f"Failed to parse CrossRef response: {e}")
    
    def _get_arxiv_bibtex(self, arxiv_id: str) -> str:
        """Generate BibTeX from arXiv API for arXiv ID."""
        if not REQUESTS_AVAILABLE:
            raise Exception("requests library not available")
            
        try:
            response = requests.get(f"{self.arxiv_url}{arxiv_id}", timeout=10)
            response.raise_for_status()
            feed = response.text
            
            # Extract title
            title_match = self.arxiv_title_pattern.search(feed)
            if title_match:
                title = title_match.group(1).split("\n")[0].strip()
            else:
                title = "Unknown Title"
            
            # Extract authors
            authors = self.arxiv_name_pattern.findall(feed)
            author_str = " and ".join(authors) if authors else "Unknown Author"
            
            # Extract publication year
            published_match = self.arxiv_published_pattern.search(feed)
            if published_match:
                try:
                    year = datetime.strptime(published_match.group(1)[:10], "%Y-%m-%d").year
                except ValueError:
                    year = "Unknown"
            else:
                year = "Unknown"
            
            return (
                f"@article{{{arxiv_id}}},\n"
                f"  title          = {{ {title} }},\n"
                f"  author         = {{ {author_str} }},\n"
                f"  year           = {{ {year} }},\n"
                f"  eprint         = {{ {arxiv_id} }},\n"
                f"  archivePrefix  = {{ arXiv }}\n"
                f"}}"
            )
            
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch arXiv data: {e}")
        except Exception as e:
            raise Exception(f"Failed to parse arXiv response: {e}")
    
    def generate_bibtex(self, identifier: str) -> str:
        """
        Generate BibTeX entry for identifier (DOI or arXiv ID).
        
        Args:
            identifier: DOI (contains "/") or arXiv ID
            
        Returns:
            BibTeX formatted string
            
        Raises:
            Exception: If generation fails
        """
        if not identifier or not identifier.strip():
            raise Exception("Empty identifier provided")
        
        identifier = identifier.strip()
        
        try:
            # DOI contains "/" while modern arXiv IDs typically don't
            if "/" in identifier:
                logger.info(f"Processing as DOI: {identifier}")
                return self._get_crossref_bibtex(identifier)
            else:
                logger.info(f"Processing as arXiv ID: {identifier}")
                return self._get_arxiv_bibtex(identifier)
                
        except Exception as e:
            logger.error(f"BibTeX generation failed for '{identifier}': {e}")
            raise

# Global instance
_generator = BibTexGenerator()

def generate_bibtex(identifier: str) -> str:
    """
    Generate BibTeX entry for DOI or arXiv ID.
    
    Args:
        identifier: DOI or arXiv identifier
        
    Returns:
        BibTeX formatted string
    """
    return _generator.generate_bibtex(identifier) 