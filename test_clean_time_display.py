#!/usr/bin/env python3
"""
Test the simplified start time display logic:
- User-set start times: show just "4pm" 
- System-selected times: show "4pm-6pm" range
"""

import requests
import json

def test_simplified_time_display():
    """Test that ONLY user-set start times display without end time"""
    
    base_url = "http://localhost:5002/sms/test"
    test_phone = "3333333333"  # Unique test number
    
    print("🕐 Testing Simplified Time Display Logic")
    print("=" * 60)
    
    # Quick setup to get to final confirmation
    print("\n1. Quick setup...")
    
    # Name
    requests.post(base_url, json={"phone_number": test_phone, "message": "Test Planner"})
    
    # Add guest
    requests.post(base_url, json={"phone_number": test_phone, "message": "1"})
    requests.post(base_url, json={"phone_number": test_phone, "message": "John Doe - 5551234567"})
    requests.post(base_url, json={"phone_number": test_phone, "message": "done"})
    
    # Availability - use a smaller window to test system-selected vs user-set
    requests.post(base_url, json={"phone_number": test_phone, "message": "Monday 6pm-8pm"})
    requests.post(base_url, json={"phone_number": test_phone, "message": "done"})
    requests.post(base_url, json={"phone_number": test_phone, "message": "John - Monday 6pm-8pm"})
    
    # Select time (this should show system-selected range)
    response = requests.post(base_url, json={"phone_number": test_phone, "message": "1"})
    result = response.json()
    print(f"\n2. After selecting system time slot:")
    print(f"Response: {result['response']}")
    
    # Set venue to get to final confirmation
    requests.post(base_url, json={"phone_number": test_phone, "message": "Pizza Palace"})
    
    print("\n3. At final confirmation with system-selected time (should show range)...")
    
    # Now test setting a specific start time via user action
    print("\n4. Using 'Set a start time' feature...")
    response = requests.post(base_url, json={
        "phone_number": test_phone,
        "message": "1"  # Set a start time
    })
    result = response.json()
    print(f"Response: {result['response']}")
    
    # Set the start time (this should trigger user_set_start_time = True)
    response = requests.post(base_url, json={
        "phone_number": test_phone,
        "message": "7pm"
    })
    result = response.json()
    print(f"\n5. After user sets start time to 7pm:")
    print(f"Response: {result['response']}")
    
    # Check the result
    response_text = result['response']
    if "🕒 Time: 7pm\n" in response_text and "7pm-" not in response_text:
        print("\n✅ SUCCESS: User-set time shows cleanly as just '7pm'")
    elif "7pm-" in response_text:
        print("\n❌ ISSUE: User-set time still showing end time")
    else:
        print(f"\n❓ Unexpected format")
        
    print(f"\nKey distinction:")
    print("• System-selected times: Should show range like '6pm-8pm'")  
    print("• User-set start times: Should show just '7pm'")
    
    print("\n🕐 Simplified Time Display Test Complete!")

if __name__ == "__main__":
    test_simplified_time_display()
