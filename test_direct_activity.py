#!/usr/bin/env python3

# Direct test of the activity collection stage

import requests
import time

base_url = "https://web-production-9a4cc.up.railway.app/sms/incoming"
planner_phone = "+15557777777"

def send_sms_test(message, description):
    print(f"\n--- {description} ---")
    print(f"Sending: '{message}'")
    
    data = {
        'From': planner_phone,
        'To': '+12792371252',
        'Body': message
    }
    
    try:
        response = requests.post(base_url, data=data, timeout=15)
        if response.status_code == 200:
            # Extract message from TwiML
            import re
            match = re.search(r'<Message>([^<]*)</Message>', response.text)
            if match:
                reply = match.group(1).strip()
                print(f"Reply: {reply}")
                return reply
            else:
                print(f"No message found in response: {response.text}")
        else:
            print(f"HTTP Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    return None

print("=== Direct Activity Test ===")

# Try a simpler approach - let's try with parentheses format
send_sms_test("restart", "Reset")
time.sleep(1)

send_sms_test("Test User", "Set name")
time.sleep(1)

# Try different guest formats
print("\n🔍 Testing different guest formats...")

# Format 1: Name, phone
reply1 = send_sms_test("John Smith, 555-123-4567", "Format 1: Name, phone")
time.sleep(1)

if "Could not find" in reply1:
    # Format 2: Name (phone)
    reply2 = send_sms_test("John Smith (555-123-4567)", "Format 2: Name (phone)")
    time.sleep(1)
    
    if "Could not find" in reply2:
        # Format 3: Name phone (no comma)
        reply3 = send_sms_test("John Smith 5551234567", "Format 3: Name phone")
        time.sleep(1)
        
        if "Could not find" in reply3:
            print("❌ None of the guest formats worked. There might be a bug in guest parsing.")
            print("Let's check if we can test the activity detection logic directly...")
            
            # Test the AI function directly via a simple hack
            # Send a message that might trigger the broad activity detection in other parts
            send_sms_test("chinese food", "Direct test of broad detection")
        else:
            print("✅ Format 3 worked! Continuing with workflow...")
    else:
        print("✅ Format 2 worked! Continuing with workflow...")
else:
    print("✅ Format 1 worked! Continuing with workflow...")

print("\n=== Test Complete ===")
