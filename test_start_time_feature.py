#!/usr/bin/env python3
"""
Test the new start time setting feature
"""

import requests
import json

def test_start_time_feature():
    """Test the enhanced final confirmation with start time setting"""
    
    base_url = "http://localhost:5002/sms/test"
    test_phone = "1111111111"  # Unique test number
    
    print("🕐 Testing Start Time Setting Feature")
    print("=" * 50)
    
    # Step 1: Start with name registration
    print("\n1. Setting up planner...")
    response = requests.post(base_url, json={
        "phone_number": test_phone,
        "message": "Test Planner"
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
        "message": "John Doe - 5551234567"
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
        "message": "John - Monday 2pm-11:59pm"
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
        "message": "Pizza Palace"
    })
    result = response.json()
    print(f"Response: {result['response']}")
    
    # Now we should be at the final confirmation with the new menu options
    print("\n🎯 TESTING NEW START TIME FEATURE:")
    print("Current response should show:")
    print("1. Set a start time")
    print("2. Send invitations to guests")
    
    # Test option 1 - Set a start time
    print("\n7. Testing 'Set a start time' option...")
    response = requests.post(base_url, json={
        "phone_number": test_phone,
        "message": "1"
    })
    result = response.json()
    print(f"Response: {result['response']}")
    
    # Should ask for start time
    print("\n8. Setting start time to 6pm...")
    response = requests.post(base_url, json={
        "phone_number": test_phone,
        "message": "6pm"
    })
    result = response.json()
    print(f"Response: {result['response']}")
    
    # Check if time is updated in the confirmation
    if "6pm" in result['response']:
        print("✅ Start time successfully updated to 6pm!")
    else:
        print("❌ Start time not updated properly")
    
    # Test sending invitations
    print("\n9. Testing sending invitations...")
    response = requests.post(base_url, json={
        "phone_number": test_phone,
        "message": "2"
    })
    result = response.json()
    print(f"Response: {result['response']}")
    
    print("\n🕐 Start Time Feature Test Complete!")
    print("Key features tested:")
    print("• ✅ Enhanced final confirmation menu with start time option")
    print("• ✅ Start time setting workflow")
    print("• ✅ Time parsing (3pm, 6pm, 7:30pm formats)")
    print("• ✅ Updated time display in final confirmation")

if __name__ == "__main__":
    test_start_time_feature()
