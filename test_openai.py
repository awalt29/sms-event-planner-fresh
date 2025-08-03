#!/usr/bin/env python3
"""
Test the deployed app's OpenAI functionality.
"""

import requests
import time

def test_openai_parsing():
    """Test if OpenAI parsing is working on the deployed app."""
    
    webhook_url = "https://web-production-9a4cc.up.railway.app/sms/incoming"
    
    # Test with a complex message that should trigger OpenAI
    test_messages = [
        "I'm free Monday morning around 10am",
        "I want to plan a dinner party next Friday evening",
        "Maybe I can do Tuesday or Wednesday afternoon",
        "I'm available between 2pm and 5pm on weekdays"
    ]
    
    print("🧪 Testing OpenAI parsing on deployed app...")
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n📝 Test {i}: '{message}'")
        
        data = {
            'From': '+15551234567',
            'Body': message
        }
        
        try:
            response = requests.post(
                webhook_url,
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ Response: {response.text[:100]}...")
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
            
        time.sleep(2)  # Brief pause between requests
    
    print("\n🎯 Test complete! Check Railway logs for any OpenAI errors.")

if __name__ == "__main__":
    test_openai_parsing()
