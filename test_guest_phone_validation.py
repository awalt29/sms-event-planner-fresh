#!/usr/bin/env python3

import requests
import time
import os

# Test that validates the phone number requirement fix
def test_guest_validation_api():
    base_url = "http://127.0.0.1:5006"
    
    # Start a new conversation
    print("Testing guest validation via API...")
    print("=" * 50)
    
    # Send initial message to start planning
    response = requests.post(f"{base_url}/sms", data={
        'From': '+15555551234',
        'Body': 'Plan an event'
    })
    
    if response.status_code != 200:
        print(f"Error starting conversation: {response.status_code}")
        return
    
    print("✅ Started event planning conversation")
    time.sleep(1)
    
    # Test case 1: Try to add guest without phone number
    print("\n1. Testing guest without phone number (should fail)...")
    response = requests.post(f"{base_url}/sms", data={
        'From': '+15555551234',
        'Body': 'Alex'
    })
    
    response_text = response.text
    print(f"Response: {response_text}")
    
    if "phone number" in response_text.lower() or "❌" in response_text:
        print("✅ CORRECTLY REJECTED guest without phone number")
    else:
        print("❌ FAILED - guest without phone number was accepted")
    
    time.sleep(1)
    
    # Test case 2: Try to add "Sarah and Mike" (should fail)  
    print("\n2. Testing 'Sarah and Mike' example (should fail)...")
    response = requests.post(f"{base_url}/sms", data={
        'From': '+15555551234', 
        'Body': 'Sarah and Mike'
    })
    
    response_text = response.text
    print(f"Response: {response_text}")
    
    if "phone number" in response_text.lower() or "❌" in response_text:
        print("✅ CORRECTLY REJECTED 'Sarah and Mike' without phone numbers")
    else:
        print("❌ FAILED - 'Sarah and Mike' was accepted without phone numbers")
    
    time.sleep(1)
    
    # Test case 3: Add guest with phone number (should work)
    print("\n3. Testing guest with phone number (should work)...")
    response = requests.post(f"{base_url}/sms", data={
        'From': '+15555551234',
        'Body': 'John Doe, 111-555-1234'
    })
    
    response_text = response.text
    print(f"Response: {response_text}")
    
    if "added" in response_text.lower() and "john doe" in response_text.lower():
        print("✅ CORRECTLY ACCEPTED guest with phone number")
    else:
        print("❌ FAILED - guest with phone number was not accepted")
    
    print("\n" + "=" * 50)
    print("Guest validation test completed!")

if __name__ == "__main__":
    test_guest_validation_api()
