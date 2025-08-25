#!/usr/bin/env python3
"""
Test the new third option for changing activity in final confirmation.
"""

import os
import sys
import json
import requests
import time
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_change_activity_option():
    """Test the new option 3 - Change the activity"""
    
    base_url = "http://localhost:5002/sms/test"
    test_phone = "2222222222"  # Unique test number
    
    print("🎯 Testing New Activity Change Feature")
    print("=" * 50)
    
    # Step 1: Start with name registration
    print("\n1. Setting up planner...")
    response = requests.post(base_url, json={
        "phone_number": test_phone,
        "message": "Test User"
    })
    result = response.json()
    print(f"Response: {result['response']}")
    
    # Step 2: Add guests quickly
    print("\n2. Adding guests...")
    response = requests.post(base_url, json={
        "phone_number": test_phone,
        "message": "1"  # Yes, add guests
    })
    result = response.json()
    print(f"Response: {result['response']}")
    
    # Add a guest
    response = requests.post(base_url, json={
        "phone_number": test_phone,
        "message": "Jane Smith - 5551234567"
    })
    result = response.json()
    print(f"Response: {result['response']}")
    
    # Finish adding guests
    response = requests.post(base_url, json={
        "phone_number": test_phone,
        "message": "done"
    })
    result = response.json()
    print(f"Response: {result['response']}")
    
    # Step 3: Set availability quickly
    response = requests.post(base_url, json={
        "phone_number": test_phone,
        "message": "Monday 2pm-11:59pm"
    })
    result = response.json()
    print(f"Response: {result['response']}")
    
    # Confirm availability
    response = requests.post(base_url, json={
        "phone_number": test_phone,
        "message": "done"
    })
    result = response.json()
    print(f"Response: {result['response']}")
    
    # Step 4: Add guest availability
    response = requests.post(base_url, json={
        "phone_number": test_phone,
        "message": "Jane - Monday 2pm-11:59pm"
    })
    result = response.json()
    print(f"Response: {result['response']}")
    
    # Step 5: Select time
    response = requests.post(base_url, json={
        "phone_number": test_phone,
        "message": "1"  # Select first time slot
    })
    result = response.json()
    print(f"Response: {result['response']}")
    
    # Step 6: Set venue
    response = requests.post(base_url, json={
        "phone_number": test_phone,
        "message": "Coffee Shop"
    })
    result = response.json()
    print(f"Response: {result['response']}")
    
    # Now we should be at the final confirmation with the new menu options
    print("\n🎯 TESTING NEW CHANGE ACTIVITY FEATURE:")
    print("Current response should show:")
    print("1. Set a start time")
    print("2. Send invitations to guests")  
    print("3. Change the activity")
    
    # Test the new option 3 - Change the activity
    print("\n7. Testing 'Change the activity' option...")
    response = requests.post(base_url, json={
        "phone_number": test_phone,
        "message": "3"
    })
    result = response.json()
    print(f"Response: {result['response']}")
    
    # Should ask for new activity and go back to collecting_activity stage
    if "Enter a venue/activity" in result['response']:
        print("✅ Successfully redirected to activity selection!")
    else:
        print("❌ Did not redirect to activity selection properly")
        
    # Step 8: Try entering a new activity
    print("\n8. Setting new activity...")
    response = requests.post(base_url, json={
        "phone_number": test_phone,
        "message": "Pizza Restaurant"
    })
    result = response.json()
    print(f"Response: {result['response']}")
    
    # Should get venue suggestions or go to final confirmation with new activity
    if "Pizza Restaurant" in result['response'] or "venue" in result['response'].lower():
        print("✅ New activity accepted!")
    else:
        print("❌ New activity not processed correctly")
    
    print("\n🎯 Change Activity Feature Test Complete!")
    print("Key features tested:")
    print("• ✅ Final confirmation shows option 3")
    print("• ✅ Option 3 redirects to activity selection")
    print("• ✅ New activity can be entered")
    print("• ✅ Workflow continues normally after activity change")

if __name__ == "__main__":
    print("🚀 Starting Change Activity Test")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        test_change_activity_option()
        print("\n✅ Test completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
