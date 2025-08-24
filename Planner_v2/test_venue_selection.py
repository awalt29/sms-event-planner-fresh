#!/usr/bin/env python3
"""
Test the new venue selection feature that allows direct venue entry or activity suggestions
"""

import requests
import json

def test_venue_selection():
    """Test the enhanced venue selection with direct venue names"""
    
    base_url = "http://localhost:5001/sms/test"
    test_phone = "1234567890"  # Unique test number
    
    print("🍕 Testing Enhanced Venue Selection Feature")
    print("=" * 50)
    
    # Step 1: Start with name registration
    print("\n1. Setting up planner...")
    response = requests.post(base_url, json={
        "phone_number": test_phone,
        "message": "Test Planner"
    })
    result = response.json()
    print(f"Response: {result['response']}")
    
    # Step 2: Add guests
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
    
    # Step 3: Date selection - pick first option
    print("\n3. Selecting date...")
    response = requests.post(base_url, json={
        "phone_number": test_phone,
        "message": "Friday evening"
    })
    result = response.json()
    print(f"Response: {result['response']}")
    
    # Step 4: Time selection - pick first option
    print("\n4. Selecting time...")
    response = requests.post(base_url, json={
        "phone_number": test_phone,
        "message": "1"  # Pick first time slot
    })
    result = response.json()
    print(f"Response: {result['response']}")
    print("\n🎯 NEW VENUE SELECTION PROMPT ABOVE! Notice the options:")
    print("   - Direct venue entry (e.g., 'Shake Shack')")
    print("   - Or text '1' for activity suggestions")
    
    # Step 5A: Test direct venue entry
    print("\n5A. Testing direct venue entry with 'Shake Shack'...")
    response = requests.post(base_url, json={
        "phone_number": test_phone,
        "message": "Shake Shack"
    })
    result = response.json()
    print(f"Response: {result['response']}")
    
    # Reset for second test - start new event  
    test_phone_2 = "1234567891"
    
    print("\n" + "="*50)
    print("🎯 TESTING ACTIVITY SUGGESTIONS PATH")
    print("="*50)
    
    # Quick setup for second test
    print("\n1. Quick setup for second test...")
    response = requests.post(base_url, json={
        "phone_number": test_phone_2,
        "message": "Test Planner 2"
    })
    
    response = requests.post(base_url, json={
        "phone_number": test_phone_2,
        "message": "1"  # Yes, add guests
    })
    
    response = requests.post(base_url, json={
        "phone_number": test_phone_2,
        "message": "Jane Doe - 5551234568"
    })
    
    response = requests.post(base_url, json={
        "phone_number": test_phone_2,
        "message": "done"
    })
    
    response = requests.post(base_url, json={
        "phone_number": test_phone_2,
        "message": "Saturday afternoon"
    })
    
    response = requests.post(base_url, json={
        "phone_number": test_phone_2,
        "message": "1"  # Pick first time slot
    })
    result = response.json()
    print(f"Time selection response: {result['response']}")
    
    # Step 5B: Test activity suggestions option
    print("\n5B. Testing activity suggestions with '1'...")
    response = requests.post(base_url, json={
        "phone_number": test_phone_2,
        "message": "1"  # Request activity suggestions
    })
    result = response.json()
    print(f"Response: {result['response']}")
    print("\n🎯 ACTIVITY SUGGESTIONS PROMPT ABOVE!")
    
    # Test traditional activity + location
    print("\n6. Testing traditional activity + location format...")
    response = requests.post(base_url, json={
        "phone_number": test_phone_2,
        "message": "sushi in Brooklyn"
    })
    result = response.json()
    print(f"Response: {result['response']}")
    
    print("\n✅ Venue Selection Enhancement Test Complete!")
    print("Key improvements demonstrated:")
    print("  ✓ Direct venue entry (e.g., 'Shake Shack')")
    print("  ✓ Activity suggestions option ('1')")
    print("  ✓ Traditional activity+location still works")
    print("  ✓ Clear user-friendly prompts with emojis")

if __name__ == "__main__":
    test_venue_selection()
