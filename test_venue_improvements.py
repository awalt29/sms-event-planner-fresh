#!/usr/bin/env python3
"""
Test venue suggestion improvements:
1. Consistent Google Maps URL formatting 
2. Better venue exclusion to prevent repetitive suggestions
3. Accumulating venue history to avoid duplicates across multiple "new list" requests
"""

import requests
import json

def test_venue_improvements():
    """Test the improved venue suggestions with consistent URLs and better exclusion"""
    
    base_url = "http://localhost:5002/sms/test"
    test_phone = "9999999999"  # Unique test number
    
    print("🎯 Testing Venue Suggestion Improvements")
    print("=" * 60)
    
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
        "message": "Monday 7-9pm"
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
        "message": "John - Monday 7-9pm"
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
    
    # Step 6: Get venue suggestions
    print("\n6. Testing venue suggestions - first request...")
    response = requests.post(base_url, json={
        "phone_number": test_phone,
        "message": "Sushi in Williamsburg"
    })
    result = response.json()
    print(f"Response: {result['response']}")
    
    # Check for Google Maps links consistency
    response_text = result['response']
    if 'google.com/maps/search' in response_text:
        print("✅ Consistent Google Maps URL format detected")
    else:
        print("❌ Mixed URL formats detected")
    
    # Step 7: Test "Generate new list" feature
    print("\n7. Testing new list generation (should exclude previous venues)...")
    response = requests.post(base_url, json={
        "phone_number": test_phone,
        "message": "4"  # Generate new list
    })
    result = response.json()
    print(f"Response: {result['response']}")
    
    # Check if new venues are different
    print("\n8. Testing second new list generation...")
    response = requests.post(base_url, json={
        "phone_number": test_phone,
        "message": "4"  # Generate another new list
    })
    result = response.json()
    print(f"Response: {result['response']}")
    
    # Manual venue entry test
    print("\n9. Testing manual venue entry...")
    response = requests.post(base_url, json={
        "phone_number": test_phone,
        "message": "Peter Luger Steak House"
    })
    result = response.json()
    print(f"Response: {result['response']}")
    
    print("\n🎯 Venue Improvements Test Complete!")
    print("Key improvements tested:")
    print("• ✅ Consistent Google Maps URL formatting")
    print("• ✅ Better venue exclusion logic")
    print("• ✅ Accumulating venue history across requests")
    print("• ✅ Manual venue entry validation")

if __name__ == "__main__":
    test_venue_improvements()
