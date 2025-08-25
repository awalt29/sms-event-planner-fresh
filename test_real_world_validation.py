#!/usr/bin/env python3
"""Test the exact real-world scenario from the screenshot"""

import requests
import json
import time

def test_gibberish_rejection():
    """Test that 'Saturday 2ydufb' is properly rejected"""
    
    webhook_url = "http://localhost:5008/sms/webhook"
    
    # Simulate the SMS message that was problematic
    test_data = {
        'From': '+12792371252',  # Guest phone number
        'Body': 'Saturday 2ydufb',  # The gibberish that should be rejected
        'To': '+12792371252'  # Your Twilio number
    }
    
    print("Testing Real-World Gibberish Rejection")
    print("=" * 50)
    print(f"Sending: '{test_data['Body']}'")
    print("-" * 30)
    
    try:
        response = requests.post(webhook_url, data=test_data)
        
        if response.status_code == 200:
            print("✅ Webhook received successfully")
            
            # Parse the TwiML response
            response_text = response.text
            print(f"Response: {response_text}")
            
            # Check if it contains error message for gibberish
            if "Could not understand your availability" in response_text:
                print("✅ SUCCESS: System properly rejected gibberish!")
                print("✅ System provided helpful error message")
            elif "Got it! Here's your availability" in response_text:
                print("❌ FAILURE: System incorrectly accepted gibberish!")
                print("❌ This should have been rejected")
            else:
                print(f"? Unknown response: {response_text}")
                
        else:
            print(f"❌ Webhook failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing webhook: {e}")

def test_valid_input_acceptance():
    """Test that valid input is still accepted"""
    
    webhook_url = "http://localhost:5008/sms/webhook"
    
    # Test with valid input
    test_data = {
        'From': '+12792371252',  
        'Body': 'Saturday afternoon',  # Valid input that should be accepted
        'To': '+12792371252'
    }
    
    print("\nTesting Valid Input Acceptance")
    print("=" * 50)
    print(f"Sending: '{test_data['Body']}'")
    print("-" * 30)
    
    try:
        # Wait a moment between tests
        time.sleep(1)
        
        response = requests.post(webhook_url, data=test_data)
        
        if response.status_code == 200:
            print("✅ Webhook received successfully")
            
            response_text = response.text
            print(f"Response: {response_text}")
            
            # Check if it properly parsed the valid input
            if "Got it! Here's your availability" in response_text:
                print("✅ SUCCESS: System properly accepted valid input!")
            elif "Could not understand your availability" in response_text:
                print("❌ FAILURE: System incorrectly rejected valid input!")
            else:
                print(f"? Unknown response: {response_text}")
                
        else:
            print(f"❌ Webhook failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing webhook: {e}")

if __name__ == "__main__":
    test_gibberish_rejection()
    test_valid_input_acceptance()
