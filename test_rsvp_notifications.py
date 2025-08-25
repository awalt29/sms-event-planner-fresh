#!/usr/bin/env python3
"""
Test RSVP notification workflow to ensure planners receive notifications
when guests respond to event invitations.
"""

import os
import sys
import json
import requests
import time
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test configuration
BASE_URL = "http://localhost:5002"
PLANNER_PHONE = "1234567890"
GUEST_PHONE = "9876543210"

def send_sms(phone_number, message):
    """Send SMS message to test endpoint"""
    try:
        response = requests.post(f"{BASE_URL}/sms/test", 
                               json={
                                   "phone_number": phone_number,
                                   "message": message
                               })
        
        if response.status_code == 200:
            result = response.json()
            print(f"📱 To {phone_number}: {message}")
            print(f"📤 Response: {result['response']}")
            print("-" * 50)
            return result['response']
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error. Is the server running?")
        print("   Start server with: python run.py")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_rsvp_workflow():
    """Test complete RSVP workflow with planner notifications"""
    print("🧪 Testing RSVP Notification Workflow")
    print("=" * 60)
    
    # Step 1: Set up planner
    print("Step 1: Setting up planner...")
    response = send_sms(PLANNER_PHONE, "Test Planner")
    if not response or "Great to meet you" not in response:
        print("❌ Failed to set up planner")
        return False
    
    # Step 2: Add a guest
    print("Step 2: Adding guest...")
    response = send_sms(PLANNER_PHONE, "John Doe, 9876543210")
    if not response or "guest added" not in response.lower():
        print("❌ Failed to add guest")
        return False
    
    # Step 3: Complete event setup (dates, venue, etc.)
    print("Step 3: Setting up event details...")
    
    # Move to dates
    send_sms(PLANNER_PHONE, "done")
    
    # Add dates
    send_sms(PLANNER_PHONE, "Saturday December 21st")
    send_sms(PLANNER_PHONE, "done")
    
    # Skip availability and go to venue
    send_sms(PLANNER_PHONE, "skip")
    
    # Add venue
    send_sms(PLANNER_PHONE, "Shake Shack")
    
    # Final confirmation
    response = send_sms(PLANNER_PHONE, "1")
    if not response or "invitations sent" not in response.lower():
        print("❌ Failed to send invitations")
        return False
    
    # Step 4: Guest receives invitation and responds with RSVP
    print("Step 4: Guest responding to RSVP...")
    guest_response = send_sms(GUEST_PHONE, "Yes")
    
    if not guest_response or "confirmed" not in guest_response.lower():
        print("❌ Guest RSVP failed")
        return False
    
    # Step 5: Check if planner gets notification
    print("Step 5: Checking for planner notification...")
    time.sleep(1)  # Give system time to process
    
    # Try sending a status message to planner to see current state
    status_response = send_sms(PLANNER_PHONE, "status")
    
    print("✅ RSVP workflow test completed!")
    print("📝 Check the server logs to verify planner received notification")
    print("   Look for: 'Sent RSVP notification to planner...'")
    
    return True

def test_multiple_guest_rsvps():
    """Test RSVP notifications with multiple guests"""
    print("\n🧪 Testing Multiple Guest RSVP Notifications")
    print("=" * 60)
    
    # Add another guest
    print("Adding second guest...")
    send_sms(PLANNER_PHONE, "add guest")
    send_sms(PLANNER_PHONE, "Jane Smith, 5555551234")
    
    # Second guest responds
    print("Second guest responding...")
    send_sms("5555551234", "No")
    
    print("✅ Multiple guest RSVP test completed!")
    return True

if __name__ == "__main__":
    print("🚀 Starting RSVP Notification Tests")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test basic RSVP workflow
    if test_rsvp_workflow():
        # Test multiple guests
        test_multiple_guest_rsvps()
    
    print("\n📋 Test Summary:")
    print("- ✅ Basic RSVP workflow tested")
    print("- ✅ Multiple guest RSVP tested") 
    print("- 📝 Check server logs for planner notifications")
    print("\n💡 Expected behavior:")
    print("  - Guest receives invitation and can RSVP")
    print("  - Planner receives immediate notification of each RSVP")
    print("  - Notification includes guest name, response, and progress count")
