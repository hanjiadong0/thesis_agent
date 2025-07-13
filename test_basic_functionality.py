#!/usr/bin/env python3
"""
Basic functionality test for Thesis Helper.

This script tests the core components of the thesis helper application
to ensure everything is working correctly.

Author: Thesis Helper Team
Date: 2024
"""

import os
import sys
import asyncio
from datetime import datetime, date

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all core modules can be imported."""
    try:
        print("🔍 Testing imports...")
        
        # Test configuration import
        from backend.app.core.config import settings, get_settings
        print("✅ Configuration module imported successfully")
        
        # Test database models
        from backend.app.models.database import Base, User, DailyProgress
        print("✅ Database models imported successfully")
        
        # Test Pydantic schemas
        from backend.app.models.schemas import UserQuestionnaireRequest, ThesisField
        print("✅ Pydantic schemas imported successfully")
        
        # Test AI service (might fail without API key)
        try:
            from backend.app.services.ai_service import ThesisAIPlannerAgent
            print("✅ AI service imported successfully")
        except ImportError as e:
            print(f"⚠️ AI service import failed: {e}")
        
        # Test email service
        from backend.app.services.email_service import EmailService
        print("✅ Email service imported successfully")
        
        print("✅ All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_configuration():
    """Test configuration loading."""
    try:
        print("\n🔧 Testing configuration...")
        
        from backend.app.core.config import settings
        
        # Test basic settings
        print(f"App Name: {settings.APP_NAME}")
        print(f"App Version: {settings.APP_VERSION}")
        print(f"Debug Mode: {settings.DEBUG}")
        print(f"AI Provider: {settings.AI_PROVIDER}")
        
        # Test API keys (don't print them fully for security)
        print(f"Notion Token: {settings.NOTION_TOKEN[:10]}...")
        print(f"Gemini API Key: {settings.GEMINI_API_KEY[:10]}...")
        print(f"Email User: {settings.EMAIL_USER}")
        
        print("✅ Configuration test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_database_models():
    """Test database model creation."""
    try:
        print("\n🗄️ Testing database models...")
        
        from backend.app.models.database import (
            Base, User, DailyProgress, UserPattern, 
            get_database_engine, create_tables
        )
        from backend.app.core.config import get_database_url
        
        # Create test database
        engine = get_database_engine(get_database_url())
        create_tables(engine)
        
        print("✅ Database tables created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_pydantic_schemas():
    """Test Pydantic schema validation."""
    try:
        print("\n📋 Testing Pydantic schemas...")
        
        from backend.app.models.schemas import (
            UserQuestionnaireRequest, ThesisField, 
            ProcrastinationLevel, WritingStyle
        )
        
        # Test valid questionnaire data
        test_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "thesis_topic": "AI in Healthcare Applications",
            "thesis_field": ThesisField.COMPUTER_SCIENCE,
            "thesis_deadline": date(2025, 12, 31),
            "daily_hours_available": 6,
            "preferred_start_time": "09:00",
            "preferred_end_time": "17:00",
            "work_days_per_week": 5,
            "procrastination_level": ProcrastinationLevel.MEDIUM,
            "focus_duration": 90,
            "writing_style": WritingStyle.DRAFT_THEN_REVISE
        }
        
        # Validate schema
        questionnaire = UserQuestionnaireRequest(**test_data)
        print(f"✅ Valid questionnaire created for: {questionnaire.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Pydantic schema test failed: {e}")
        return False

def test_ai_service():
    """Test AI service initialization."""
    try:
        print("\n🤖 Testing AI service...")
        
        from backend.app.services.ai_service import ThesisAIPlannerAgent, test_ai_connection
        
        # Test AI service initialization
        ai_agent = ThesisAIPlannerAgent()
        print("✅ AI agent initialized successfully")
        
        # Test AI connection (might fail without valid API key)
        try:
            connection_ok = test_ai_connection()
            if connection_ok:
                print("✅ AI connection test passed")
            else:
                print("⚠️ AI connection test failed (check API key)")
        except Exception as e:
            print(f"⚠️ AI connection test failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ AI service test failed: {e}")
        return False

def test_email_service():
    """Test email service initialization."""
    try:
        print("\n📧 Testing email service...")
        
        from backend.app.services.email_service import EmailService, test_email_connection
        
        # Test email service initialization
        email_service = EmailService()
        print("✅ Email service initialized successfully")
        
        # Test email connection (might fail without valid credentials)
        try:
            connection_ok = test_email_connection()
            if connection_ok:
                print("✅ Email connection test passed")
            else:
                print("⚠️ Email connection test failed (check credentials)")
        except Exception as e:
            print(f"⚠️ Email connection test failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Email service test failed: {e}")
        return False

def test_fastapi_health():
    """Test FastAPI health endpoint."""
    try:
        print("\n🌐 Testing FastAPI health endpoint...")
        
        # This is a basic import test since we can't run the server here
        from backend.app.main import app
        print("✅ FastAPI app imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ FastAPI test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🎓 Thesis Helper - Basic Functionality Test")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Configuration Test", test_configuration),
        ("Database Models Test", test_database_models),
        ("Pydantic Schemas Test", test_pydantic_schemas),
        ("AI Service Test", test_ai_service),
        ("Email Service Test", test_email_service),
        ("FastAPI Test", test_fastapi_health),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Your thesis helper is ready to use!")
        print("\n🚀 Next steps:")
        print("1. Set up your .env file with API keys")
        print("2. Run: source venv/bin/activate && python -m uvicorn backend.app.main:app --reload")
        print("3. Open http://localhost:8000 in your browser")
    else:
        print("⚠️ Some tests failed. Check the error messages above.")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 