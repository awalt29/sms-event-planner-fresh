#!/usr/bin/env python3
import requests
import time

# Test the complete workflow to see where chinese food might be timing out
phone_number = "+15551234567"
base_url = "https://web-production-9a4cc.up.railway.app/sms/incoming"

def send_sms_test(message, description):
    print(f"\n--- {description} ---")
    print(f"Sending: '{message}'")
    
    data = {
        'From': phone_number,
        'To': '+12792371252',
        'Body': message
    }
    
    try:
        response = requests.post(base_url, data=data, timeout=10)
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

# Test sequence - simulate a user trying "chinese food"
print("=== Testing Broad Activity Detection ===")

# First, test as initial message
send_sms_test("chinese food", "Initial message test")

time.sleep(1)

# Test as part of planning flow
send_sms_test("plan event", "Start planning")
time.sleep(1)

# Add a guest (to progress through workflow)
send_sms_test("John Doe, 555-123-4567", "Add guest")
time.sleep(1)

# Continue to dates
send_sms_test("done", "Finish adding guests")
time.sleep(1)

# Add dates
send_sms_test("Saturday", "Add dates")
time.sleep(1)

# Choose option 1 to continue
send_sms_test("1", "Request availability")
time.sleep(2)

# Simulate guest responding (would need different phone)
# send_sms_test("Saturday 2pm-5pm", "Guest availability") 

# Continue to location (assuming we can skip availability for testing)
# This would need to be done with proper guest responses in real scenario
