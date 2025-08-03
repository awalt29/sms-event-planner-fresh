#!/usr/bin/env python3
"""
Test script to update Twilio webhook using environment variables.
"""

import os
from twilio.rest import Client

def update_webhook():
    """Update Twilio webhook with environment variables."""
    try:
        # Get credentials from environment
        sid = os.getenv('TWILIO_SID')
        auth = os.getenv('TWILIO_AUTH') 
        number = os.getenv('TWILIO_NUMBER')
        
        if not all([sid, auth, number]):
            print("❌ Missing Twilio environment variables")
            print("Set TWILIO_SID, TWILIO_AUTH, and TWILIO_NUMBER")
            return False
            
        webhook_url = "https://web-production-9a4cc.up.railway.app/sms/incoming"
        
        print("🔧 Updating Twilio webhook...")
        print(f"Number: {number}")
        print(f"Webhook: {webhook_url}")
        
        # Initialize client
        client = Client(sid, auth)
        
        # Find phone number
        phone_numbers = client.incoming_phone_numbers.list()
        target_number = None
        
        for num in phone_numbers:
            if num.phone_number == number:
                target_number = num
                break
                
        if not target_number:
            print(f"❌ Phone number {number} not found")
            return False
            
        # Update webhook
        target_number.update(sms_url=webhook_url)
        print(f"✅ Successfully updated webhook!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = update_webhook()
    if success:
        print("\n🎉 Ready to receive SMS messages!")
    else:
        print("\n❌ Failed to update webhook.")
