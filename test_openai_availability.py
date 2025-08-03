#!/usr/bin/env python3
"""
Test OpenAI availability parsing specifically.
This creates a guest state and triggers the actual OpenAI parsing function.
"""

import requests
import time

def test_availability_parsing():
    """Test the specific OpenAI availability parsing that was failing."""
    
    webhook_url = "https://web-production-9a4cc.up.railway.app/sms/incoming"
    
    print("🧪 Testing OpenAI availability parsing (the actual failing function)...")
    
    # Step 1: Create planner and event
    print("\n📝 Step 1: Create planner")
    planner_phone = "+15551111111"
    response = requests.post(webhook_url, data={
        'From': planner_phone,
        'Body': 'I want to plan a birthday party'
    }, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    print(f"Planner creation: {response.text[:100]}...")
    time.sleep(1)
    
    # Provide planner name
    response = requests.post(webhook_url, data={
        'From': planner_phone,
        'Body': 'Aaron'
    }, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    print(f"Name provided: {response.text[:100]}...")
    time.sleep(1)
    
    # Add guest details to create guest state
    response = requests.post(webhook_url, data={
        'From': planner_phone,
        'Body': 'Sarah Johnson, 555-222-3333'
    }, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    print(f"Guest added: {response.text[:100]}...")
    time.sleep(1)
    
    # Finish guest collection
    response = requests.post(webhook_url, data={
        'From': planner_phone,
        'Body': 'done'
    }, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    print(f"Guests done: {response.text[:100]}...")
    time.sleep(2)
    
    # Step 2: Now respond as a guest with complex availability (TRIGGERS OPENAI)
    print("\n📝 Step 2: Guest responds with complex availability (TRIGGERS OpenAI parse_availability)")
    guest_phone = "+15552223333"
    
    # This should trigger parse_availability() which uses OpenAI
    complex_availability_messages = [
        "I'm flexible but prefer Saturday evening around 6pm to 8pm",
        "I could possibly do Monday morning between 10am and noon or Wednesday evening",
        "Maybe I can do Tuesday after 2pm or Friday morning",
        "I'm available next weekend but prefer Sunday afternoon"
    ]
    
    for i, availability_msg in enumerate(complex_availability_messages, 1):
        print(f"\n🤖 Testing availability message {i} (triggers OpenAI):")
        print(f"Message: '{availability_msg}'")
        
        response = requests.post(webhook_url, data={
            'From': guest_phone,
            'Body': availability_msg
        }, headers={'Content-Type': 'application/x-www-form-urlencoded'})
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        if response.status_code == 500:
            print("❌ ERROR 500 - OpenAI 'proxies' issue still exists!")
            return False
        elif response.status_code == 200:
            print("✅ No error - OpenAI parsing may be working")
        
        time.sleep(2)
    
    print("\n🎯 OpenAI availability parsing test complete!")
    print("✅ If all responses were 200, OpenAI integration is working")
    print("❌ If any 500 errors occurred, the 'proxies' issue persists")
    
    return True

if __name__ == "__main__":
    test_availability_parsing()
