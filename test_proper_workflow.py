#!/usr/bin/env python3

# Better test script to properly reach the activity selection stage

import requests
import time

base_url = "https://web-production-9a4cc.up.railway.app/sms/incoming"

def send_sms_test(phone, message, description):
    print(f"\n--- {description} ---")
    print(f"From {phone}: '{message}'")
    
    data = {
        'From': phone,
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

# Use different phone numbers for planner and guest
planner_phone = "+15551234567"
guest_phone = "+15559876543"

print("=== Testing Activity Selection Stage (Proper Workflow) ===")

# Reset any existing sessions first
send_sms_test(planner_phone, "restart", "Reset planner")
time.sleep(1)

# Step 1: Start as planner with name
send_sms_test(planner_phone, "Test Planner", "1. Planner sets name")
time.sleep(1)

# Step 2: Add a guest with proper format
send_sms_test(planner_phone, "Jane Smith, 555-123-4567", "2. Add guest")
time.sleep(1)

# Step 3: Finish adding guests
send_sms_test(planner_phone, "done", "3. Finish guests")
time.sleep(1)

# Step 4: Add dates
send_sms_test(planner_phone, "Saturday and Sunday", "4. Add dates")
time.sleep(1)

# Step 5: Send availability requests (option 1)
send_sms_test(planner_phone, "1", "5. Send availability requests")
time.sleep(2)

# Step 6: Simulate guest responding with availability
send_sms_test(guest_phone, "Saturday 2pm-5pm, Sunday all day", "6. Guest responds with availability")
time.sleep(2)

# Step 7: Planner picks a time (option 1 - should show timeslots)
send_sms_test(planner_phone, "1", "7. Planner picks time")
time.sleep(1)

# Step 8: Select first timeslot
send_sms_test(planner_phone, "1", "8. Select timeslot 1")
time.sleep(1)

# Step 9: Add location
send_sms_test(planner_phone, "Manhattan", "9. Add location")
time.sleep(1)

# Step 10: THIS IS THE CRITICAL TEST - Activity selection
print("\n🎯 CRITICAL TEST: Testing 'chinese food' at activity selection stage")
reply = send_sms_test(planner_phone, "chinese food", "10. TEST: chinese food activity")

if reply and "chinese food" in reply.lower() and ("broad" in reply.lower() or "specific" in reply.lower()):
    print("\n✅ SUCCESS: Broad activity detection is working!")
    print("The system correctly detected 'chinese food' as too broad.")
elif reply and "timeout" in reply.lower():
    print("\n❌ PROBLEM: Still getting timeouts instead of broad detection.")
elif reply and "venue" in reply.lower():
    print("\n❌ PROBLEM: System bypassed broad detection and went to venues.")
else:
    print("\n❓ UNCLEAR: Got unexpected response.")
    print(f"Response was: {reply}")

print("\n=== Test Complete ===")
