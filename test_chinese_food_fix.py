#!/usr/bin/env python3

import requests
import time

# Test the Chinese food fix
def test_chinese_food_workflow():
    base_url = "https://web-production-9a4cc.up.railway.app/sms/incoming"
    planner_phone = "+15557777777"
    system_phone = "+12792371252"
    
    def send_sms(message):
        """Send SMS and return response"""
        response = requests.post(base_url, data={
            'From': planner_phone,
            'To': system_phone,
            'Body': message
        })
        return response.text
    
    print("🧪 Testing Chinese food fix...")
    print("=" * 50)
    
    # Step 1: Start conversation
    response = send_sms("hey")
    print(f"1. Started conversation: {response}")
    time.sleep(1)
    
    # Step 2: Provide name
    response = send_sms("TestUser")
    print(f"2. Provided name: {response}")
    time.sleep(1)
    
    # Step 3: Add guest
    response = send_sms("John Smith (555-123-4567)")
    print(f"3. Added guest: {response}")
    time.sleep(1)
    
    # Step 4: Continue to dates
    response = send_sms("done")
    print(f"4. Moved to dates: {response}")
    time.sleep(1)
    
    # Step 5: Provide dates
    response = send_sms("Saturday")
    print(f"5. Provided dates: {response}")
    time.sleep(1)
    
    # Step 6: Request availability
    response = send_sms("1")
    print(f"6. Requested availability: {response}")
    time.sleep(1)
    
    # Step 7: Guest responds to availability (simulate from guest phone)
    guest_response = requests.post(base_url, data={
        'From': "+15551234567",  # Guest's phone
        'To': system_phone,
        'Body': "Saturday 2pm-5pm"
    })
    print(f"7. Guest provided availability: {guest_response.text}")
    time.sleep(1)
    
    # Step 8: Guest confirms
    guest_confirm = requests.post(base_url, data={
        'From': "+15551234567",  # Guest's phone
        'To': system_phone,
        'Body': "1"
    })
    print(f"8. Guest confirmed: {guest_confirm.text}")
    time.sleep(1)
    
    # Step 9: Planner picks time
    response = send_sms("1")
    print(f"9. Planner picked time: {response}")
    time.sleep(1)
    
    # Step 10: Planner selects time slot
    response = send_sms("1")
    print(f"10. Selected timeslot: {response}")
    time.sleep(1)
    
    # Step 11: Provide location
    response = send_sms("Manhattan")
    print(f"11. Provided location: {response}")
    time.sleep(1)
    
    # Step 12: TEST CHINESE FOOD - This is the critical test!
    print("\n🎯 CRITICAL TEST: Testing 'Chinese food'...")
    response = send_sms("Chinese food")
    print(f"12. CHINESE FOOD TEST: {response}")
    
    # Check if the response contains the expected broad detection message
    if "is a bit broad" in response and "Chinese restaurant" in response:
        print("\n✅ SUCCESS! Chinese food broad detection is working!")
        return True
    else:
        print("\n❌ FAILED! Chinese food detection not working properly.")
        print(f"Expected: Message containing 'is a bit broad' and 'Chinese restaurant'")
        print(f"Got: {response}")
        return False

if __name__ == "__main__":
    test_chinese_food_workflow()
