#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ocr.py
~~~~~~
Convert images to LaTeX code using pix2tex.
Adapted for the thesis helper system with proper error handling.
"""

from __future__ import annotations

import logging
import os
from typing import Optional, Tuple
from pathlib import Path

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None

try:
    from pix2tex.cli import LatexOCR
    PIX2TEX_AVAILABLE = True
except ImportError:
    PIX2TEX_AVAILABLE = False
    LatexOCR = None

logger = logging.getLogger(__name__)

class LaTeXOCRService:
    """LaTeX OCR service for converting mathematical images to LaTeX code."""
    
    def __init__(self):
        self.model = None
        self._initialized = False
        
        if PIX2TEX_AVAILABLE and PIL_AVAILABLE:
            self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the pix2tex model."""
        try:
            logger.info("Loading pix2tex LaTeX OCR model...")
            self.model = LatexOCR()
            self._initialized = True
            logger.info("LaTeX OCR model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load LaTeX OCR model: {e}")
            self._initialized = False
    
    def image_to_latex(self, file_path: str) -> Tuple[str, str]:
        """
        Convert an image file to LaTeX code.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Tuple of (latex_code, status_message)
        """
        if not PIL_AVAILABLE or not PIX2TEX_AVAILABLE:
            return "", "OCR dependencies (PIL and pix2tex) not available"
        
        if not self._initialized:
            return "", "LaTeX OCR model not initialized"
        
        if not file_path or not os.path.exists(file_path):
            return "", "Image file not found"
        
        try:
            # Validate image file
            path = Path(file_path)
            if path.suffix.lower() not in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif']:
                return "", "Unsupported image format. Please use PNG, JPG, or other common formats."
            
            # Load and process image
            logger.info(f"Processing image: {file_path}")
            img = Image.open(file_path)
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Perform OCR
            latex_code = self.model(img)
            
            if latex_code and latex_code.strip():
                logger.info(f"Successfully converted image to LaTeX: {len(latex_code)} characters")
                return latex_code, "Successfully converted image to LaTeX"
            else:
                return "", "No LaTeX code extracted from image"
                
        except Exception as e:
            logger.error(f"Error during LaTeX OCR: {e}")
            return "", f"Error processing image: {str(e)}"
    
    def is_available(self) -> bool:
        """Check if OCR service is available."""
        return self._initialized and PIL_AVAILABLE and PIX2TEX_AVAILABLE

# Global instance
_ocr_service = LaTeXOCRService()

def image_to_latex(file_path: str) -> Tuple[str, str]:
    """
    Convert an image file to LaTeX code.
    
    Args:
        file_path: Path to the image file
        
    Returns:
        Tuple of (latex_code, status_message)
    """
    return _ocr_service.image_to_latex(file_path)

def is_ocr_available() -> bool:
    """Check if OCR functionality is available."""
    return _ocr_service.is_available() 