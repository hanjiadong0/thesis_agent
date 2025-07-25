#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task Helper Tools Module

This module provides various AI-powered tools to assist students with their thesis work,
including AI detection, bibliography generation, research assistance, and academic writing support.
"""

# Original tools
from .ai_detector import detect_ai_content, AIDetector
from .bibtex_generator import generate_bibtex, BibTexGenerator  
from .semantic_scholar import get_paper_metadata, search_papers, SemanticScholarAPI
from .ocr import image_to_latex, is_ocr_available, LaTeXOCRService
from .pdf_summarizer import pdf_to_summary, create_pdf_summarizer, PDFSummarizer
from .ethics_system import EthicsTracker, TaskEthicsManager

# New tools
from .grammar_checker import check_grammar_and_style, create_grammar_checker, GrammarStyleChecker
from .web_search import search_web, fact_check, verify_source, create_web_search_service, WebSearchService
from .wikipedia_lookup import search_wikipedia, get_article_summary, get_topic_overview, create_wikipedia_service, WikipediaLookupService
from .survey_helper import generate_survey_questions, create_data_collection_plan, create_survey_helper, SurveyDataHelper
from .math_solver import solve_equation, calculate_expression, convert_units, solve_statistics, create_math_solver, MathSolver

__all__ = [
    # Original tools
    'detect_ai_content',
    'AIDetector',
    'generate_bibtex', 
    'BibTexGenerator',
    'get_paper_metadata',
    'search_papers',
    'SemanticScholarAPI',
    'image_to_latex',
    'is_ocr_available',
    'LaTeXOCRService',
    'pdf_to_summary',
    'create_pdf_summarizer',
    'PDFSummarizer',
    'EthicsTracker',
    'TaskEthicsManager',
    
    # New tools
    'check_grammar_and_style',
    'create_grammar_checker',
    'GrammarStyleChecker',
    'search_web',
    'fact_check',
    'verify_source',
    'create_web_search_service',
    'WebSearchService',
    'search_wikipedia',
    'get_article_summary', 
    'get_topic_overview',
    'create_wikipedia_service',
    'WikipediaLookupService',
    'generate_survey_questions',
    'create_data_collection_plan',
    'create_survey_helper',
    'SurveyDataHelper',
    'solve_equation',
    'calculate_expression',
    'convert_units',
    'solve_statistics',
    'create_math_solver',
    'MathSolver'
] 