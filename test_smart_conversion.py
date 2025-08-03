#!/usr/bin/env python3

import requests
import time

def test_chinese_food_smart_conversion():
    """Test that 'chinese food' now works with smart conversion"""
    base_url = "https://web-production-9a4cc.up.railway.app/sms/incoming"
    planner_phone = "+15556666666"  # Different number for clean test
    system_phone = "+12792371252"
    
    def send_sms(message):
        """Send SMS and return response"""
        response = requests.post(base_url, data={
            'From': planner_phone,
            'To': system_phone,
            'Body': message
        })
        return response.text
    
    print("🧪 Testing Smart Chinese Food Conversion...")
    print("=" * 60)
    
    # Complete workflow to activity stage
    steps = [
        ("Start conversation", "hey"),
        ("Provide name", "TestUser2"),
        ("Add guest", "Jane Doe (555-987-6543)"),
        ("Move to dates", "done"),
        ("Provide dates", "Saturday"),
        ("Request availability", "1")
    ]
    
    for step_name, message in steps:
        response = send_sms(message)
        print(f"✓ {step_name}: Success")
        time.sleep(1)
    
    # Have guest respond with availability
    guest_response = requests.post(base_url, data={
        'From': "+15559876543",
        'To': system_phone,
        'Body': "Saturday 3pm-6pm"
    })
    print("✓ Guest provided availability")
    time.sleep(1)
    
    guest_confirm = requests.post(base_url, data={
        'From': "+15559876543",
        'To': system_phone,
        'Body': "1"
    })
    print("✓ Guest confirmed availability")
    time.sleep(1)
    
    # Planner workflow continuation
    continuation_steps = [
        ("Pick time", "1"),
        ("Select timeslot", "1"),
        ("Set location", "Manhattan")
    ]
    
    for step_name, message in continuation_steps:
        response = send_sms(message)
        print(f"✓ {step_name}: Success")
        time.sleep(1)
    
    # THE CRITICAL TEST: Chinese food
    print("\n🎯 CRITICAL TEST: Testing 'Chinese food' with smart conversion...")
    response = send_sms("Chinese food")
    
    # Check for success indicators
    success_indicators = [
        "Perfect! Looking for",
        "Chinese",
        "Here are some great options",
        "Select an option"
    ]
    
    if all(indicator in response for indicator in success_indicators):
        print("✅ SUCCESS! 'Chinese food' now works with smart conversion!")
        print(f"Response contains venue suggestions as expected")
        return True
    else:
        print("❌ FAILED! Smart conversion not working properly")
        print(f"Response: {response}")
        return False

if __name__ == "__main__":
    test_chinese_food_smart_conversion()
