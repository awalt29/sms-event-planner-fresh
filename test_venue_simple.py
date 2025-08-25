#!/usr/bin/env python3
"""
Simple test focused on venue selection functionality
"""

import requests
import json

def test_venue_simple():
    """Simple test to get to venue selection quickly"""
    
    base_url = "http://localhost:5001/sms/test"
    test_phone = "9999999999"  # Unique test number
    
    print("🍕 Simple Venue Selection Test")
    print("=" * 40)
    
    # Step 1: Name
    print("\n1. Setting up planner...")
    response = requests.post(base_url, json={
        "phone_number": test_phone,
        "message": "Test User"
    })
    result = response.json()
    print(f"✓ {result['response'][:50]}...")
    
    # Step 2: Skip guests for now
    print("\n2. Adding a guest...")
    response = requests.post(base_url, json={
        "phone_number": test_phone,
        "message": "1"  # Yes, add guests
    })
    result = response.json()
    
    # Try simple guest format
    response = requests.post(base_url, json={
        "phone_number": test_phone,
        "message": "John 5551234567"
    })
    result = response.json()
    print(f"Guest add: {result['response'][:50]}...")
    
    # Finish guests
    response = requests.post(base_url, json={
        "phone_number": test_phone,
        "message": "done"
    })
    result = response.json()
    print(f"✓ {result['response'][:50]}...")
    
    # Step 3: Quick date
    print("\n3. Setting date...")
    response = requests.post(base_url, json={
        "phone_number": test_phone,
        "message": "Friday evening"
    })
    result = response.json()
    print(f"✓ {result['response'][:50]}...")
    
    # Step 4: Time - pick first option
    print("\n4. Selecting time...")
    response = requests.post(base_url, json={
        "phone_number": test_phone,
        "message": "1"
    })
    result = response.json()
    print(f"✓ Time response: {result['response']}")
    
    print("\n🎯 VENUE SELECTION PHASE:")
    
    # Step 5: Test direct venue entry
    print("\n5. Testing 'Shake Shack' (direct venue)...")
    response = requests.post(base_url, json={
        "phone_number": test_phone,
        "message": "Shake Shack"
    })
    result = response.json()
    print(f"✓ Venue response: {result['response']}")
    
    print("\n✅ Test Complete!")

if __name__ == "__main__":
    test_venue_simple()
