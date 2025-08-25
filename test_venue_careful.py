#!/usr/bin/env python3
"""
Test venue selection with careful phone number handling
"""

import requests
import json

def test_venue_careful():
    """Test with carefully managed phone numbers"""
    
    base_url = "http://localhost:5001/sms/test"
    planner_phone = "+15555551111"
    guest_phone = "+15555552222"
    
    print("🎯 Careful Venue Selection Test")
    print("=" * 50)
    
    # Phase 1: Planner setup
    print("\n📋 PHASE 1: Planner Setup")
    
    response = requests.post(base_url, json={
        "phone_number": planner_phone,
        "message": "Gatherly User"
    })
    result = response.json()
    print(f"✓ Planner: {result['response'][:40]}...")
    
    # Add guest with same phone format
    response = requests.post(base_url, json={
        "phone_number": planner_phone,
        "message": "1"  # Add guests
    })
    
    response = requests.post(base_url, json={
        "phone_number": planner_phone,
        "message": f"Test Guest {guest_phone}"
    })
    result = response.json()
    print(f"✓ Guest: {result['response'][:40]}...")
    
    response = requests.post(base_url, json={
        "phone_number": planner_phone,
        "message": "done"
    })
    
    # Set dates
    response = requests.post(base_url, json={
        "phone_number": planner_phone,
        "message": "Friday and Saturday"
    })
    result = response.json()
    print(f"✓ Dates: {result['response'][:40]}...")
    
    # Send availability
    response = requests.post(base_url, json={
        "phone_number": planner_phone,
        "message": "1"  # Send requests
    })
    result = response.json()
    print(f"✓ Sent: {result['response']}")
    
    # Phase 2: Guest responds with EXACT same phone number
    print(f"\n👤 PHASE 2: Guest Response from {guest_phone}")
    
    response = requests.post(base_url, json={
        "phone_number": guest_phone,
        "message": "I can do both days"
    })
    result = response.json()
    print(f"✓ Guest: {result['response']}")
    
    # Check planner status
    print(f"\n⏰ PHASE 3: Check planner status")
    response = requests.post(base_url, json={
        "phone_number": planner_phone,
        "message": "status"
    })
    result = response.json()
    print(f"✓ Status: {result['response']}")
    
    print("\n✅ Test shows the current state of venue selection workflow")

if __name__ == "__main__":
    test_venue_careful()
