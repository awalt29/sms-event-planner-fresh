#!/usr/bin/env python3
"""Test what availability request message gets generated on the live system"""

import requests
import urllib.parse

def test_availability_message_format():
    """Simulate the full workflow and check what message format is used"""
    
    # Railway URL that works
    base_url = "https://web-production-faa49.up.railway.app/sms/webhook"
    
    # Headers for SMS webhook
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    # Use a fresh phone number to avoid conflicts
    planner_phone = "+15559998877"
    
    # Step 1: Start new event
    print("🚀 Step 1: Starting new event...")
    response = requests.post(base_url, headers=headers, data={
        "From": planner_phone,
        "To": "+15559876543",
        "Body": "start party"
    })
    print(f"Response: {response.text}")
    
    # Step 2: Provide name
    print("\n👤 Step 2: Providing name...")
    response = requests.post(base_url, headers=headers, data={
        "From": planner_phone,
        "To": "+15559876543", 
        "Body": "Test Planner"
    })
    print(f"Response: {response.text}")
    
    # Step 3: Add multiple guests
    print("\n👥 Step 3: Adding guests...")
    guests = [
        "Sarah Johnson, 555-111-1111",
        "Alex Chen, 555-222-2222", 
        "Mike Davis, 555-333-3333"
    ]
    
    for i, guest in enumerate(guests, 1):
        print(f"   Adding guest {i}: {guest}")
        response = requests.post(base_url, headers=headers, data={
            "From": planner_phone,
            "To": "+15559876543",
            "Body": urllib.parse.quote_plus(guest)
        })
        print(f"   Response: {response.text}")
    
    # Step 4: Finish guest collection
    print("\n✅ Step 4: Finishing guest collection...")
    response = requests.post(base_url, headers=headers, data={
        "From": planner_phone,
        "To": "+15559876543",
        "Body": "done"
    })
    print(f"Response: {response.text}")
    
    # Step 5: Set dates
    print("\n📅 Step 5: Setting dates...")
    response = requests.post(base_url, headers=headers, data={
        "From": planner_phone,
        "To": "+15559876543",
        "Body": "Friday and Saturday"
    })
    print(f"Response: {response.text}")
    
    # Step 6: Request availability (this should use our new format!)
    print("\n💌 Step 6: Requesting availability - CHECK FOR GUEST LIST!")
    response = requests.post(base_url, headers=headers, data={
        "From": planner_phone,
        "To": "+15559876543",
        "Body": "1"
    })
    print(f"Response: {response.text}")
    
    # Now simulate a guest responding to see what message they got
    print("\n📱 Step 7: Simulating guest response to see their message...")
    # Try responding as Sarah (should have received availability request)
    response = requests.post(base_url, headers=headers, data={
        "From": "+15551111111",  # Sarah's number
        "To": "+15559876543",
        "Body": "Friday all day"
    })
    print(f"Guest response handled: {response.text}")
    
    print("\n" + "="*60)
    print("🔍 ANALYSIS:")
    print("- The availability requests were sent in step 6")
    print("- Each guest (Sarah, Alex, Mike) should have received:")
    print("  • Date list")  
    print("  • 👥 With: [other guests] <- THE NEW FEATURE")
    print("  • Instructions")
    print("- If no guest list appeared, there might be a deployment issue")
    print("="*60)

if __name__ == "__main__":
    test_availability_message_format()
