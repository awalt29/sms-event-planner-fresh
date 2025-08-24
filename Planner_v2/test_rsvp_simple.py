#!/usr/bin/env python3
"""
Simple test to demonstrate RSVP guest state cleanup issue
"""

import os
import sys
import json
import requests
import time

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE_URL = "http://localhost:5002"

def send_test_message(phone, message):
    """Send test message via /sms/test endpoint"""
    try:
        response = requests.post(f"{BASE_URL}/sms/test", 
                               json={
                                   "phone_number": phone,
                                   "message": message
                               },
                               timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            print(f"📱 {phone}: {message}")
            print(f"📤 Response: {result['response']}")
            print("-" * 50)
            return result['response']
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error. Is the server running on port 5002?")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_rsvp_guest_state_cleanup():
    """Test the specific RSVP guest state cleanup issue"""
    print("🧪 Testing RSVP Guest State Cleanup")
    print("=" * 50)
    
    planner_phone = "2125551001"
    guest_phone = "2125551002"
    
    # Step 1: Planner creates event
    print("Step 1: Planner creates event...")
    response = send_test_message(planner_phone, "Test User")
    if not response:
        return False
    
    response = send_test_message(planner_phone, "Test Guest, 2125551002")
    if not response:
        return False
    
    response = send_test_message(planner_phone, "done")
    if not response:
        return False
    
    # Step 2: Move through workflow to get to RSVP stage
    print("Step 2: Complete event setup...")
    
    # Dates
    response = send_test_message(planner_phone, "Tomorrow")
    if not response:
        return False
    
    response = send_test_message(planner_phone, "done")
    if not response:
        return False
    
    # Skip availability collection if needed
    response = send_test_message(planner_phone, "1")  # Continue with planning
    if not response:
        return False
    
    # Time selection
    response = send_test_message(planner_phone, "1")  # All day or first option
    if not response:
        return False
    
    # Location
    response = send_test_message(planner_phone, "My house")
    if not response:
        return False
    
    # Activity
    response = send_test_message(planner_phone, "Birthday party")
    if not response:
        return False
    
    # Skip venue or confirm final
    response = send_test_message(planner_phone, "1")  # Confirm/send invites
    if not response:
        return False
    
    print("Step 3: Guest receives invitation and responds...")
    
    # Step 3: Guest responds to RSVP
    response = send_test_message(guest_phone, "Yes")
    
    if not response:
        return False
    
    print("Step 4: Guest sends another message (should not get RSVP prompt again)...")
    
    # Step 4: Guest sends another message - this should NOT get RSVP prompt
    response = send_test_message(guest_phone, "Hey")
    
    if "Yes" in response or "No" in response or "Maybe" in response or "confirm your attendance" in response:
        print("❌ FAILED: Guest is still getting RSVP prompts after responding!")
        print(f"   Response: {response}")
        return False
    else:
        print("✅ SUCCESS: Guest state was cleaned up properly!")
        print(f"   Response: {response}")
        return True

if __name__ == "__main__":
    success = test_rsvp_guest_state_cleanup()
    if success:
        print("\n🎉 Test passed - RSVP cleanup is working!")
    else:
        print("\n💥 Test failed - RSVP cleanup needs fixing!")
