#!/usr/bin/env python3
"""
Test venue display in final confirmation
"""

import requests
import json

def test_venue_display():
    """Test that selected venue appears in final confirmation"""
    
    base_url = "http://localhost:5001/sms/test"
    test_phone = "+15555558888"
    
    print("🍕 Testing Venue Display in Final Confirmation")
    print("=" * 50)
    
    # Quick setup to get to venue selection
    print("\n1. Quick setup...")
    
    # Name
    requests.post(base_url, json={"phone_number": test_phone, "message": "Test User"})
    
    # Add guest
    requests.post(base_url, json={"phone_number": test_phone, "message": "1"})
    requests.post(base_url, json={"phone_number": test_phone, "message": "John 5551234567"})
    requests.post(base_url, json={"phone_number": test_phone, "message": "done"})
    
    # Set date
    requests.post(base_url, json={"phone_number": test_phone, "message": "Friday evening"})
    
    # Send availability
    requests.post(base_url, json={"phone_number": test_phone, "message": "1"})
    
    # Simulate guest response
    requests.post(base_url, json={"phone_number": "+15551234567", "message": "Friday works"})
    
    # Time selection
    requests.post(base_url, json={"phone_number": test_phone, "message": "1"})
    
    print("✓ Setup complete")
    
    # THE KEY TEST: Venue selection and confirmation display
    print("\n2. 🎯 Testing 'Shake Shack' venue selection...")
    response = requests.post(base_url, json={
        "phone_number": test_phone,
        "message": "Shake Shack"
    })
    result = response.json()
    print(f"Final confirmation message:")
    print(f"{result['response']}")
    
    # Check if venue appears correctly
    if "Shake Shack" in result['response']:
        print("\n✅ SUCCESS: Venue 'Shake Shack' appears in confirmation!")
    else:
        print("\n❌ ISSUE: Venue 'Shake Shack' missing from confirmation")
    
    print("\n✅ Test Complete!")

if __name__ == "__main__":
    test_venue_display()
