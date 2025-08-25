#!/usr/bin/env python3
"""Test availability parsing end-to-end"""

import requests
import json

def test_availability_parsing():
    """Test sending 'Friday 7-11p' to the SMS endpoint"""
    
    # Webhook URL (assuming ngrok or local testing)
    webhook_url = "http://localhost:5002/sms/webhook"
    
    # Test data - simulate Twilio webhook for guest availability response
    test_data = {
        'From': '+12793625555',  # Test guest phone
        'Body': 'Friday 7-11p',
        'To': '+your-twilio-number'  # Your Twilio number
    }
    
    try:
        response = requests.post(webhook_url, data=test_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        # Look for success indicators
        if "couldn't understand" in response.text.lower():
            print("❌ FAILED - Still getting parsing error")
        elif "7" in response.text and "11" in response.text:
            print("✅ SUCCESS - Time range appears to be parsed")
        else:
            print("🤔 UNCLEAR - Response doesn't show clear success or failure")
            
    except Exception as e:
        print(f"Error testing: {e}")

if __name__ == "__main__":
    print("=== Testing 'Friday 7-11p' parsing ===")
    test_availability_parsing()
