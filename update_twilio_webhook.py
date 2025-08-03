#!/usr/bin/env python3
"""
Script to update Twilio webhook URL after deployment.
Run this after deploying to update your Twilio phone number's webhook URL.
"""

import os
from twilio.rest import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def update_webhook_url(new_base_url):
    """Update Twilio webhook URL for the configured phone number."""
    
    # Get Twilio credentials
    account_sid = os.environ.get('TWILIO_SID')
    auth_token = os.environ.get('TWILIO_AUTH')
    phone_number = os.environ.get('TWILIO_NUMBER')
    
    if not all([account_sid, auth_token, phone_number]):
        print("❌ Missing Twilio credentials in environment variables")
        return False
    
    try:
        # Initialize Twilio client
        client = Client(account_sid, auth_token)
        
        # Construct webhook URL
        webhook_url = f"{new_base_url.rstrip('/')}/sms/incoming"
        
        # Find and update the phone number
        phone_numbers = client.incoming_phone_numbers.list()
        
        target_number = None
        for number in phone_numbers:
            if number.phone_number == phone_number:
                target_number = number
                break
        
        if not target_number:
            print(f"❌ Phone number {phone_number} not found in your Twilio account")
            return False
        
        # Update the webhook URL
        target_number.update(sms_url=webhook_url)
        
        print(f"✅ Successfully updated webhook URL to: {webhook_url}")
        print(f"📱 Phone number: {phone_number}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating webhook: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Twilio Webhook Updater")
    print("=" * 40)
    
    # Get the new base URL
    base_url = input("Enter your deployed app URL (e.g., https://your-app.railway.app): ").strip()
    
    if not base_url:
        print("❌ Base URL is required")
        exit(1)
    
    if not base_url.startswith(('http://', 'https://')):
        print("❌ URL must start with http:// or https://")
        exit(1)
    
    # Update the webhook
    success = update_webhook_url(base_url)
    
    if success:
        print("\n🎉 Webhook updated successfully!")
        print("Your app is now ready to receive SMS messages.")
    else:
        print("\n❌ Failed to update webhook. Please check your credentials and try again.")