#!/usr/bin/env python3
"""
Direct test of OpenAI functions to check if 'proxies' error still occurs.
This bypasses SMS workflow and directly calls the AI functions.
"""

import os
import sys
import logging

# Add the app directory to Python path
sys.path.insert(0, '/Users/aaronwalters/Planner_app_live')

from app import create_app
from app.utils.ai import AIService, parse_availability, parse_event_input

# Set up logging to see errors
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_direct_openai_calls():
    """Test OpenAI functions directly to see if 'proxies' error occurs."""
    
    print("🧪 DIRECT OpenAI Function Test")
    print("Testing the exact functions that were failing with 'proxies' error...")
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        print("\n📋 Testing environment...")
        print(f"OpenAI API Key set: {'Yes' if app.config.get('OPENAI_API_KEY') else 'No'}")
        
        # Test 1: Initialize AI Service
        print("\n🤖 Test 1: Initialize AIService")
        try:
            ai_service = AIService()
            ai_service._initialize_client()
            
            if ai_service.client is None:
                print("❌ OpenAI client failed to initialize")
                return False
            else:
                print("✅ OpenAI client initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing AI service: {e}")
            return False
        
        # Test 2: Parse Event Input (triggers OpenAI chat completion)
        print("\n📅 Test 2: Parse Event Input (triggers OpenAI)")
        try:
            event_result = parse_event_input(
                "I want to plan a birthday party next Saturday evening for about 15 people"
            )
            print(f"✅ Event parsing successful: {event_result}")
        except Exception as e:
            print(f"❌ Error in parse_event_input: {e}")
            if "'proxies'" in str(e):
                print("🚨 FOUND THE PROXIES ERROR!")
                return False
        
        # Test 3: Parse Availability (triggers OpenAI chat completion)
        print("\n⏰ Test 3: Parse Availability (triggers OpenAI)")
        test_availability_messages = [
            "I'm free Monday morning around 10am",
            "I could possibly do Tuesday after 2pm or Friday evening",
            "Maybe I can do weekend afternoons between 1pm and 5pm"
        ]
        
        for i, msg in enumerate(test_availability_messages, 1):
            try:
                print(f"\n   Testing availability {i}: '{msg}'")
                availability_result = parse_availability(msg, {
                    'event_notes': 'Birthday party',
                    'current_date': '2025-08-03'
                })
                print(f"   ✅ Availability parsing successful: {availability_result.get('confidence', 'unknown')}")
            except Exception as e:
                print(f"   ❌ Error in parse_availability: {e}")
                if "'proxies'" in str(e):
                    print("   🚨 FOUND THE PROXIES ERROR!")
                    return False
        
        print("\n🎉 ALL DIRECT OPENAI TESTS PASSED!")
        print("✅ The 'proxies' error appears to be resolved!")
        return True

if __name__ == "__main__":
    success = test_direct_openai_calls()
    if success:
        print("\n✅ OpenAI integration is working correctly")
    else:
        print("\n❌ OpenAI integration still has issues")
