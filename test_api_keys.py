#!/usr/bin/env python3
"""
Quick test script to verify API keys are working.
Run this after setting up your .env file.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_environment():
    """Test if environment variables are loaded correctly."""
    print("🔍 Testing Environment Variables...")
    
    from backend.app.core.config import settings
    
    tests = [
        ("GEMINI_API_KEY", settings.GEMINI_API_KEY, True),  # Required
        ("EMAIL_USER", settings.EMAIL_USER, False),        # Optional  
        ("NOTION_TOKEN", settings.NOTION_TOKEN, False),    # Optional
    ]
    
    all_good = True
    
    for name, value, required in tests:
        if value and value != f"your_{name.lower()}_here":
            print(f"✅ {name}: Configured")
        elif required:
            print(f"❌ {name}: MISSING (Required)")
            all_good = False
        else:
            print(f"⚪ {name}: Not configured (Optional)")
    
    return all_good

def test_gemini_connection():
    """Test Gemini AI connection."""
    print("\n🤖 Testing Gemini AI Connection...")
    
    try:
        from backend.app.services.ai_service import ThesisAIPlannerAgent
        
        # Try to initialize the AI agent
        ai_agent = ThesisAIPlannerAgent()
        print("✅ Gemini AI service initialized successfully")
        
        # Try a simple AI call
        import google.generativeai as genai
        from backend.app.core.config import settings
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Say 'Hello from Gemini!'")
        
        print(f"✅ Gemini AI response: {response.text.strip()}")
        return True
        
    except Exception as e:
        print(f"❌ Gemini AI test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🎓 Thesis Helper - API Key Test")
    print("=" * 40)
    
    # Test environment
    env_ok = test_environment()
    
    if not env_ok:
        print("\n❌ Please set up your GEMINI_API_KEY in the .env file first!")
        return False
    
    # Test Gemini connection
    gemini_ok = test_gemini_connection()
    
    print("\n" + "=" * 40)
    if gemini_ok:
        print("🎉 All tests passed! Your thesis helper is ready to use!")
        print("\n🚀 You can now:")
        print("1. Go to http://localhost:3000")
        print("2. Fill out the questionnaire") 
        print("3. Generate your personalized thesis timeline")
    else:
        print("❌ Tests failed. Please check your API key configuration.")
    
    return gemini_ok

if __name__ == "__main__":
    success = main() 