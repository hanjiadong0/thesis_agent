#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pdf_summarizer.py
~~~~~~~~~~~~~~~~~
Extract text from PDFs and generate summaries using AI.
Adapted for the thesis helper system to use our existing AI service.
"""

from __future__ import annotations

import logging
import itertools
from pathlib import Path
from typing import List, Optional, Tuple, Any

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    fitz = None

logger = logging.getLogger(__name__)

class PDFSummarizer:
    """PDF text extraction and summarization service."""
    
    def __init__(self, ai_service=None):
        """
        Initialize PDF summarizer.
        
        Args:
            ai_service: AI service instance for generating summaries
        """
        self.ai_service = ai_service
        self.max_chunk_tokens = 3000  # Conservative limit for most models
    
    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract all text from a PDF file."""
        if not PYMUPDF_AVAILABLE:
            raise Exception("PyMuPDF not available")
        
        if not file_path or not Path(file_path).exists():
            raise Exception("PDF file not found")
        
        try:
            doc = fitz.open(file_path)
            full_text = ""
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                if text.strip():  # Only add non-empty pages
                    full_text += f"\n--- Page {page_num + 1} ---\n{text}"
            
            doc.close()
            
            if not full_text.strip():
                raise Exception("No text content found in PDF")
            
            logger.info(f"Extracted {len(full_text)} characters from PDF")
            return full_text.strip()
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise
    
    def _chunk_text(self, text: str, max_words_per_chunk: int = 800) -> List[str]:
        """Split text into manageable chunks for summarization."""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), max_words_per_chunk):
            chunk = " ".join(words[i:i + max_words_per_chunk])
            chunks.append(chunk)
        
        return chunks
    
    def _generate_ai_summary(self, text: str, max_length: int = 300) -> str:
        """Generate summary using our AI service."""
        if not self.ai_service:
            return "AI service not available"
        
        try:
            # Create a summarization prompt
            prompt = f"""Please provide a concise academic summary of the following text. Focus on the main points, key findings, and important conclusions. Keep the summary to approximately {max_length} words.

Text to summarize:
{text}

Summary:"""
            
            # Use our AI service to generate summary
            if hasattr(self.ai_service, '_call_ollama'):
                # Ollama
                response = self.ai_service._call_ollama(prompt)
            elif hasattr(self.ai_service, '_call_gemini'):
                # Gemini
                response = self.ai_service._call_gemini(prompt)
            else:
                return "AI service method not recognized"
            
            return response.strip() if response else "Failed to generate summary"
            
        except Exception as e:
            logger.error(f"Error generating AI summary: {e}")
            return f"Error generating summary: {str(e)}"
    
    def pdf_to_summary(
        self, 
        file_path: str,
        max_summary_length: int = 300,
        max_chunks: int = 5,
        bullet_format: bool = True
    ) -> Tuple[str, str]:
        """
        Extract text from PDF and return a summary.
        
        Args:
            file_path: Path to PDF file
            max_summary_length: Maximum words per chunk summary
            max_chunks: Maximum number of chunks to process
            bullet_format: Whether to format as bullet points
            
        Returns:
            Tuple of (summary, status_message)
        """
        if not PYMUPDF_AVAILABLE:
            return "", "PyMuPDF dependency not available"
        
        if not self.ai_service:
            return "", "AI service not available"
        
        try:
            # Extract text from PDF
            full_text = self._extract_text_from_pdf(file_path)
            
            # Split into chunks
            chunks = self._chunk_text(full_text)
            
            if not chunks:
                return "", "No text chunks extracted from PDF"
            
            # Limit number of chunks to process
            chunks_to_process = chunks[:max_chunks]
            logger.info(f"Processing {len(chunks_to_process)} chunks out of {len(chunks)} total")
            
            # Generate summaries for each chunk
            summaries = []
            for i, chunk in enumerate(chunks_to_process):
                logger.info(f"Summarizing chunk {i+1}/{len(chunks_to_process)}")
                summary = self._generate_ai_summary(chunk, max_summary_length)
                if summary and summary.strip():
                    summaries.append(summary)
            
            if not summaries:
                return "", "No summaries generated"
            
            # Format the final summary
            if bullet_format:
                final_summary = "\n• " + "\n• ".join(summaries)
            else:
                final_summary = "\n\n".join(summaries)
            
            status = f"Successfully summarized {len(chunks_to_process)} sections from PDF"
            if len(chunks) > max_chunks:
                status += f" (processed {max_chunks} of {len(chunks)} sections)"
            
            return final_summary, status
            
        except Exception as e:
            logger.error(f"Error in PDF summarization: {e}")
            return "", f"Error: {str(e)}"
    
    def extract_text_only(self, file_path: str) -> Tuple[str, str]:
        """
        Extract raw text from PDF without summarization.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Tuple of (extracted_text, status_message)
        """
        try:
            text = self._extract_text_from_pdf(file_path)
            return text, f"Successfully extracted {len(text)} characters"
        except Exception as e:
            return "", f"Error extracting text: {str(e)}"

# Function to create instance with AI service
def create_pdf_summarizer(ai_service) -> PDFSummarizer:
    """Create PDFSummarizer instance with AI service."""
    return PDFSummarizer(ai_service)

# Convenience functions (require AI service to be passed)
def pdf_to_summary(file_path: str, ai_service, **kwargs) -> Tuple[str, str]:
    """
    Summarize PDF using AI service.
    
    Args:
        file_path: Path to PDF file
        ai_service: AI service instance
        **kwargs: Additional arguments for pdf_to_summary
        
    Returns:
        Tuple of (summary, status_message)
    """
    summarizer = PDFSummarizer(ai_service)
    return summarizer.pdf_to_summary(file_path, **kwargs) 