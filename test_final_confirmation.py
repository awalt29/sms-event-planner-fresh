#!/usr/bin/env python3
"""
Test the final confirmation fix for venue selection
"""

import requests
import json

def test_final_confirmation():
    """Test that venue selection leads to proper final confirmation"""
    
    base_url = "http://localhost:5001/sms/test"
    planner_phone = "+15555559999"
    
    print("🎉 Testing Final Confirmation After Venue Selection")
    print("=" * 55)
    
    # Quick setup
    print("\n1. Quick event setup...")
    
    # Name
    response = requests.post(base_url, json={
        "phone_number": planner_phone,
        "message": "Test Planner"
    })
    
    # Add guests  
    response = requests.post(base_url, json={
        "phone_number": planner_phone,
        "message": "1"  # Add guests
    })
    
    response = requests.post(base_url, json={
        "phone_number": planner_phone,
        "message": "John 5551234567"
    })
    
    response = requests.post(base_url, json={
        "phone_number": planner_phone,
        "message": "done"
    })
    
    # Set dates
    response = requests.post(base_url, json={
        "phone_number": planner_phone,
        "message": "Friday evening"
    })
    
    # Send availability requests
    response = requests.post(base_url, json={
        "phone_number": planner_phone,
        "message": "1"
    })
    
    print("✓ Event setup complete")
    
    # Simulate guest response to get to time selection
    print("\n2. Simulating guest response...")
    response = requests.post(base_url, json={
        "phone_number": "+15551234567",
        "message": "I can do Friday evening"
    })
    
    # Time selection (as planner)
    print("\n3. Selecting time...")
    response = requests.post(base_url, json={
        "phone_number": planner_phone,
        "message": "1"  # Pick first time option
    })
    result = response.json()
    print(f"Time selection: {result['response'][:60]}...")
    
    # THE KEY TEST: Venue selection
    print("\n4. 🍕 Testing venue selection with 'Shake Shack'...")
    response = requests.post(base_url, json={
        "phone_number": planner_phone,
        "message": "Shake Shack"
    })
    result = response.json()
    print(f"Venue response:\n{result['response']}")
    
    # Test the confirmation
    print("\n5. 🎯 Testing 'Yes' response for final confirmation...")
    response = requests.post(base_url, json={
        "phone_number": planner_phone,
        "message": "Yes"
    })
    result = response.json()
    print(f"Final confirmation result:\n{result['response']}")
    
    print("\n✅ Test Complete!")
    print("Expected behavior:")
    print("  ✓ After 'Shake Shack': Shows full event summary with date/time/venue/guests")
    print("  ✓ After 'Yes': Sends invitations and confirms event is finalized")

if __name__ == "__main__":
    test_final_confirmation()
