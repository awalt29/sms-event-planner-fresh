#!/usr/bin/env python3

# Complete workflow test to reach activity stage

import requests
import time

base_url = "https://web-production-9a4cc.up.railway.app/sms/incoming"
planner_phone = "+15557777777"
guest_phone = "+15551234567"  # This is the guest we added

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

print("=== Complete Workflow Test ===")

# Step 1: Reset and start fresh
send_sms_test(planner_phone, "restart", "1. Reset")
time.sleep(1)

# Step 2: Set name
send_sms_test(planner_phone, "Test Planner", "2. Set name")
time.sleep(1)

# Step 3: Add guest with correct format
send_sms_test(planner_phone, "John Smith (555-123-4567)", "3. Add guest")
time.sleep(1)

# Step 4: Finish adding guests
send_sms_test(planner_phone, "done", "4. Done adding guests")
time.sleep(1)

# Step 5: Add dates
send_sms_test(planner_phone, "Saturday", "5. Add dates")
time.sleep(1)

# Step 6: Send availability requests (option 1)
send_sms_test(planner_phone, "1", "6. Send availability requests")
time.sleep(2)

# Step 7: Guest responds with availability
send_sms_test(guest_phone, "Saturday 2pm-5pm", "7. Guest responds")
time.sleep(2)

# Step 8: Planner picks time (option 1)
send_sms_test(planner_phone, "1", "8. Pick time")
time.sleep(1)

# Step 9: Select first timeslot
send_sms_test(planner_phone, "1", "9. Select first timeslot")
time.sleep(1)

# Step 10: Add location
send_sms_test(planner_phone, "Manhattan", "10. Add location")
time.sleep(1)

# Step 11: THE CRITICAL TEST - Activity with "chinese food"
print("\n🎯 CRITICAL TEST: Activity selection with 'chinese food'")
reply = send_sms_test(planner_phone, "chinese food", "11. TEST: chinese food")

# Analyze the response
if reply and "chinese food" in reply.lower() and ("broad" in reply.lower() or "specific" in reply.lower()):
    print("\n✅ SUCCESS: Broad activity detection is working!")
    print("The system correctly detected 'chinese food' as too broad.")
elif reply and "timeout" in reply.lower():
    print("\n❌ PROBLEM: Still getting AI timeouts instead of broad detection.")
elif reply and ("venue" in reply.lower() or "option" in reply.lower()):
    print("\n❌ PROBLEM: System bypassed broad detection and went to venue suggestions.")
    print("This means the broad detection is NOT working at the activity stage.")
else:
    print("\n❓ UNCLEAR RESULT:")
    print(f"Response: {reply}")

print("\n=== Test Complete ===")
