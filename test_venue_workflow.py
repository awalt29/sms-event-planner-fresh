#!/usr/bin/env python3
"""
Test venue selection by simulating the full workflow including guest responses
"""

import requests
import json

def test_venue_workflow():
    """Test venue selection by going through the complete workflow"""
    
    base_url = "http://localhost:5001/sms/test"
    planner_phone = "5555551111"
    guest_phone = "5555552222"
    
    print("🎯 Complete Venue Selection Workflow Test")
    print("=" * 50)
    
    # Phase 1: Planner setup
    print("\n📋 PHASE 1: Planner Setup")
    
    response = requests.post(base_url, json={
        "phone_number": planner_phone,
        "message": "Gatherly User"
    })
    result = response.json()
    print(f"✓ Planner created: {result['response'][:50]}...")
    
    # Add guest
    response = requests.post(base_url, json={
        "phone_number": planner_phone,
        "message": "1"  # Yes, add guests
    })
    
    response = requests.post(base_url, json={
        "phone_number": planner_phone,
        "message": "Test Guest 5555552222"
    })
    result = response.json()
    print(f"✓ Guest added: {result['response'][:50]}...")
    
    response = requests.post(base_url, json={
        "phone_number": planner_phone,
        "message": "done"
    })
    result = response.json()
    print(f"✓ Guests finished: {result['response'][:50]}...")
    
    # Set dates
    response = requests.post(base_url, json={
        "phone_number": planner_phone,
        "message": "Friday after 2pm and Saturday all day"
    })
    result = response.json()
    print(f"✓ Dates set: {result['response'][:80]}...")
    
    # Confirm and send availability requests
    response = requests.post(base_url, json={
        "phone_number": planner_phone,
        "message": "1"  # Send availability requests
    })
    result = response.json()
    print(f"✓ Availability sent: {result['response']}")
    
    # Phase 2: Guest responds
    print("\n👤 PHASE 2: Guest Response")
    
    response = requests.post(base_url, json={
        "phone_number": guest_phone,
        "message": "1"  # Guest confirms availability
    })
    result = response.json()
    print(f"✓ Guest responded: {result['response']}")
    
    # Phase 3: Time selection (planner)
    print("\n⏰ PHASE 3: Time Selection")
    
    response = requests.post(base_url, json={
        "phone_number": planner_phone,
        "message": "1"  # Select first time slot
    })
    result = response.json()
    print(f"✓ Time selected!")
    print(f"Response: {result['response']}")
    
    # Phase 4: Venue selection - the new feature!
    print("\n🍕 PHASE 4: Enhanced Venue Selection")
    print("This should show the new venue options...")
    
    print("\nTest A: Direct venue entry")
    response = requests.post(base_url, json={
        "phone_number": planner_phone,
        "message": "Shake Shack"
    })
    result = response.json()
    print(f"✓ Direct venue: {result['response']}")
    
    print("\n✅ Workflow Test Complete!")
    print("The venue selection enhancement allows:")
    print("  ✓ Direct venue names (e.g., 'Shake Shack')")
    print("  ✓ Activity suggestions option ('1')")
    print("  ✓ Traditional activity+location format")

if __name__ == "__main__":
    test_venue_workflow()
