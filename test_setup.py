#!/usr/bin/env python3
"""
Test script to verify the setup is working correctly
"""

import asyncio
import logging
from config.settings import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_components():
    """Test all major components"""
    
    print("🔧 Testing Auto Job Application System Setup...")
    
    # Test 1: Settings
    print("\n1. Testing Settings...")
    try:
        print(f"   ✅ API Host: {settings.API_HOST}")
        print(f"   ✅ API Port: {settings.API_PORT}")
        print(f"   ✅ Groq Model: {settings.GROQ_MODEL}")
        print(f"   ✅ SMTP Server: {settings.SMTP_SERVER}")
        print(f"   ✅ Supported Job Sites: {settings.SUPPORTED_JOB_SITES}")
    except Exception as e:
        print(f"   ❌ Settings Error: {e}")
        return False
    
    # Test 2: Import services
    print("\n2. Testing Service Imports...")
    try:
        from services.job_scraper import JobScraper
        from services.email_generator import EmailGenerator
        from services.email_sender import EmailSender
        from services.crew_manager import CrewManager
        print("   ✅ All services imported successfully")
    except Exception as e:
        print(f"   ❌ Service Import Error: {e}")
        return False
    
    # Test 3: Initialize services
    print("\n3. Testing Service Initialization...")
    try:
        email_generator = EmailGenerator()
        print("   ✅ Email Generator initialized")
        
        email_sender = EmailSender()
        print("   ✅ Email Sender initialized")
        
        # Note: JobScraper and CrewManager might take longer due to WebDriver setup
        print("   ⏳ Initializing Job Scraper (this may take a moment)...")
        job_scraper = JobScraper()
        print("   ✅ Job Scraper initialized")
        
        print("   ⏳ Initializing Crew Manager (this may take a moment)...")
        crew_manager = CrewManager()
        print("   ✅ Crew Manager initialized")
        
    except Exception as e:
        print(f"   ❌ Service Initialization Error: {e}")
        return False
    
    # Test 4: Test Groq connection
    print("\n4. Testing Groq Connection...")
    try:
        from groq import Groq
        client = Groq(api_key=settings.GROQ_API_KEY)
        
        # Simple test request
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[{"role": "user", "content": "Hello, this is a test."}],
            max_tokens=10
        )
        print("   ✅ Groq API connection successful")
        
    except Exception as e:
        print(f"   ❌ Groq Connection Error: {e}")
        return False
    
    # Test 5: Test SMTP connection
    print("\n5. Testing SMTP Connection...")
    try:
        if email_sender.test_connection():
            print("   ✅ SMTP connection successful")
        else:
            print("   ⚠️  SMTP connection failed (check credentials)")
    except Exception as e:
        print(f"   ❌ SMTP Test Error: {e}")
    
    print("\n🎉 Setup test completed!")
    print("\nNext steps:")
    print("1. Run 'python main.py' to start the API server")
    print("2. Visit http://localhost:8000/docs for API documentation")
    print("3. Test the endpoints using the examples in README.md")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_components()) 