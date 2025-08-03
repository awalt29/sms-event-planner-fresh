#!/usr/bin/env python3

import requests
import time

def test_final_chinese_food_fix():
    """Final test to verify Chinese food works end-to-end"""
    base_url = "https://web-production-9a4cc.up.railway.app/sms/incoming"
    planner_phone = "+15558888888"  # Clean test number
    system_phone = "+12792371252"
    
    def send_sms(message):
        """Send SMS and return response"""
        response = requests.post(base_url, data={
            'From': planner_phone,
            'To': system_phone,
            'Body': message
        })
        return response.text
    
    print("🧪 FINAL TEST: Chinese Food SMS Flow Fix...")
    print("=" * 60)
    
    # Quick workflow to activity stage
    steps = [
        ("Start", "hey"),
        ("Name", "FinalTester"),
        ("Guest", "Bob Smith (555-888-9999)"),
        ("Dates", "done"),
        ("Provide dates", "Saturday"),
        ("Request availability", "1")
    ]
    
    for step_name, message in steps:
        response = send_sms(message)
        print(f"✓ {step_name}")
        time.sleep(0.5)
    
    # Guest responds
    guest_response = requests.post(base_url, data={
        'From': "+15558889999",
        'To': system_phone,
        'Body': "Saturday 4pm-7pm"
    })
    time.sleep(0.5)
    
    guest_confirm = requests.post(base_url, data={
        'From': "+15558889999", 
        'To': system_phone,
        'Body': "1"
    })
    print("✓ Guest availability provided")
    time.sleep(0.5)
    
    # Continue to activity stage
    final_steps = [
        ("Pick time", "1"),
        ("Select slot", "1"), 
        ("Location", "Manhattan")
    ]
    
    for step_name, message in final_steps:
        response = send_sms(message)
        print(f"✓ {step_name}")
        time.sleep(0.5)
    
    # THE ULTIMATE TEST: Chinese food
    print("\n🎯 ULTIMATE TEST: Chinese food in SMS flow...")
    response = send_sms("chinese food")
    
    # Check for venue suggestions (success) vs error message (failure)
    if "Perfect! Looking for" in response and "Here are some great options" in response:
        print("✅ SUCCESS! Chinese food works perfectly in SMS flow!")
        print("✅ Old broad detection removed successfully!")
        return True
    elif "is a bit broad" in response:
        print("❌ FAILED! Still hitting old broad detection")
        print(f"Response: {response}")
        return False
    else:
        print(f"❓ Unexpected response: {response}")
        return False

if __name__ == "__main__":
    test_final_chinese_food_fix()
