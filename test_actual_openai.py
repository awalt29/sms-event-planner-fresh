#!/usr/bin/env python3
"""
Test the specific OpenAI functionality that was failing.
This tests the actual conversation flow where OpenAI parsing occurs.
"""

import requests
import time

def test_openai_conversation_flow():
    """Test the full conversation flow that triggers OpenAI parsing."""
    
    webhook_url = "https://web-production-9a4cc.up.railway.app/sms/incoming"
    test_phone = "+15551234567"
    
    print("🧪 Testing ACTUAL OpenAI usage in conversation flow...")
    
    # Step 1: Start event planning (should trigger OpenAI event parsing)
    print("\n📝 Step 1: Starting event planning (triggers OpenAI event parsing)")
    response = requests.post(webhook_url, data={
        'From': test_phone,
        'Body': 'I want to plan a birthday party for my daughter next Saturday evening with about 15 people'
    }, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    
    print(f"Response: {response.text[:150]}...")
    time.sleep(2)
    
    # Step 2: Provide name
    print("\n📝 Step 2: Providing name")
    response = requests.post(webhook_url, data={
        'From': test_phone,
        'Body': 'Aaron'
    }, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    
    print(f"Response: {response.text[:150]}...")
    time.sleep(2)
    
    # Step 3: Add a guest (this should create guest records)
    print("\n📝 Step 3: Adding a guest")
    response = requests.post(webhook_url, data={
        'From': test_phone,
        'Body': 'Add Sarah (555-123-4567)'
    }, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    
    print(f"Response: {response.text[:150]}...")
    time.sleep(2)
    
    # Step 4: Test availability parsing as a guest (should trigger OpenAI)
    print("\n📝 Step 4: Guest providing availability (triggers OpenAI availability parsing)")
    response = requests.post(webhook_url, data={
        'From': '+15551234567',  # Different number (guest)
        'Body': 'I am flexible but prefer Saturday evening around 6pm to 8pm or maybe Sunday afternoon'
    }, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    
    print(f"Response: {response.text[:150]}...")
    time.sleep(2)
    
    # Step 5: Try another complex availability message
    print("\n📝 Step 5: Another complex availability message")
    response = requests.post(webhook_url, data={
        'From': '+15551234567',
        'Body': 'I could possibly do Monday morning between 10am and noon or Wednesday evening'
    }, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    
    print(f"Response: {response.text[:150]}...")
    
    print("\n🎯 Test complete!")
    print("✅ If no 500 errors occurred, OpenAI integration is working")
    print("❌ If you see 500 errors, OpenAI 'proxies' issue still exists")

if __name__ == "__main__":
    test_openai_conversation_flow()
