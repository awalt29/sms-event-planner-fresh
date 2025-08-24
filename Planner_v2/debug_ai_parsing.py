#!/usr/bin/env python3
"""Test AI parsing specifically for 'Friday 7-11p'"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_ai_parsing_debug():
    """Test the AI parsing flow step by step"""
    
    # Check if we have OpenAI API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found - this explains why AI parsing fails!")
        print("   The system falls back to simple parsing when AI is unavailable.")
        return
    else:
        print(f"✅ OPENAI_API_KEY found: {api_key[:8]}...")

    # Test the validation first
    message = "Friday 7-11p"
    print(f"Testing message: '{message}'")
    
    # Simulate context that would be passed
    context = {
        'event_dates': ['2025-08-22', '2025-08-23']  # Example Friday and Saturday
    }
    print(f"Context: {context}")
    
    # Check validation (we know this should pass now)
    import re
    pattern = r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\s+\d{1,2}(:\d{2})?\s*(am?|pm?)?\s*(-|to)\s*\d{1,2}(:\d{2})?\s*(am?|pm?)\b'
    match = re.search(pattern, message.lower())
    if match:
        print("✅ Validation passes - would reach AI parsing")
    else:
        print("❌ Validation fails - would not reach AI parsing")
        return
    
    # Test if AI service would be called
    try:
        from app.services.ai_processing_service import AIProcessingService
        ai_service = AIProcessingService()
        
        if not ai_service.api_key:
            print("❌ AI service has no API key - explains fallback to simple parsing")
            return
            
        print("✅ AI service initialized successfully")
        
        # Would need to test actual API call, but that requires the full context
        print("🔍 AI parsing would be attempted with full prompt")
        
    except Exception as e:
        print(f"❌ Error initializing AI service: {e}")

def analyze_failure_points():
    """Analyze the main failure points for AI parsing"""
    print("\n=== AI Parsing Failure Analysis ===")
    print("Main reasons why AI parser might fail and use simple fallback:")
    print()
    print("1. 🔑 Missing OPENAI_API_KEY environment variable")
    print("   - Most common cause")
    print("   - AI service returns None immediately")
    print()
    print("2. 🌐 Network/API issues")
    print("   - OpenAI API timeout (30s)")
    print("   - Rate limiting")
    print("   - Service outage")
    print()
    print("3. 📝 Malformed JSON response from AI")
    print("   - AI returns non-JSON text")
    print("   - JSON parsing fails")
    print("   - No JSON regex match found")
    print()
    print("4. 🚫 Pre-validation rejection (FIXED)")
    print("   - Input rejected before AI parsing")
    print("   - Fixed by updating regex patterns")
    print()
    print("5. ❓ Missing context data")
    print("   - No event_dates in context")
    print("   - AI can't map day names to dates")
    
    # Check the most likely culprit
    if not os.getenv('OPENAI_API_KEY'):
        print("\n🎯 MOST LIKELY CAUSE: Missing OPENAI_API_KEY")
        print("   The AI parser fails immediately, forcing simple parser fallback")
    else:
        print(f"\n✅ OPENAI_API_KEY is present: {os.getenv('OPENAI_API_KEY', '')[:8]}...")

if __name__ == "__main__":
    test_ai_parsing_debug()
    analyze_failure_points()
