#!/usr/bin/env python3

# Test script to simulate reaching the activity selection stage and testing "chinese food"

import requests
import time
import json

base_url = "https://web-production-9a4cc.up.railway.app/sms/incoming"
phone_number = "+15551111111"  # Use a different number for testing

def send_sms_test(message, description):
    print(f"\n--- {description} ---")
    print(f"Sending: '{message}'")
    
    data = {
        'From': phone_number,
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

print("=== Testing Activity Selection Stage ===")

# Step 1: Start with a name
print("\n🚀 Starting complete workflow to reach activity selection...")
send_sms_test("Test User", "1. Set name")
time.sleep(1)

# Step 2: Add a guest
send_sms_test("John Doe, 555-123-4567", "2. Add guest")
time.sleep(1)

# Step 3: Finish adding guests
send_sms_test("done", "3. Finish adding guests")
time.sleep(1)

# Step 4: Add dates
send_sms_test("Saturday", "4. Add dates")
time.sleep(1)

# Step 5: Request availability (option 1)
send_sms_test("1", "5. Request availability")
time.sleep(2)

# Step 6: Since we need to simulate guest responses, let's try to force progression
# In a real scenario, we'd need the guest to respond with availability
# For testing, let's try to use the planner account to simulate having availability

# Let's try to pick a time (assuming we can bypass availability for testing)
# This might not work, but let's see what happens
send_sms_test("1", "6. Try to pick a time")
time.sleep(1)

# Step 7: Add location
send_sms_test("Manhattan", "7. Add location")
time.sleep(1)

# Step 8: THIS IS THE KEY TEST - Activity selection with "chinese food"
print("\n🎯 CRITICAL TEST: Testing 'chinese food' at activity selection stage")
reply = send_sms_test("chinese food", "8. TEST ACTIVITY: chinese food")

if reply and "chinese food" in reply.lower() and ("broad" in reply.lower() or "specific" in reply.lower()):
    print("\n✅ SUCCESS: Broad activity detection is working!")
    print("The system correctly detected 'chinese food' as too broad.")
else:
    print("\n❌ PROBLEM: Broad activity detection may not be working properly.")
    print("Expected a message about being too broad, but got different response.")

print("\n=== Test Complete ===")
