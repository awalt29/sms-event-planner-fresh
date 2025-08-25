#!/usr/bin/env python3
"""
Test script for deployed SMS Event Planner
Usage: python test_deployed_app.py https://your-app.railway.app
"""

import requests
import sys
import json

def test_deployed_app(base_url):
    """Test the deployed application"""
    
    print(f"🧪 Testing deployed app at: {base_url}")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health check passed!")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test 2: API root
    print("\n2. Testing API root...")
    try:
        response = requests.get(base_url, timeout=10)
        if response.status_code == 200:
            print("✅ API root accessible!")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ API root failed: {response.status_code}")
    except Exception as e:
        print(f"⚠️  API root error: {e}")
    
    # Test 3: SMS test endpoint
    print("\n3. Testing SMS functionality...")
    try:
        test_data = {
            "phone_number": "5551234567",
            "message": "Test User"
        }
        response = requests.post(
            f"{base_url}/sms/test", 
            json=test_data,
            timeout=10,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SMS test passed!")
            print(f"   Response: {result.get('response', '')[:100]}...")
            
            # Test guest addition
            print("\n4. Testing guest addition...")
            guest_data = {
                "phone_number": "5551234567", 
                "message": "Alice Smith, 555-999-8888"
            }
            response = requests.post(
                f"{base_url}/sms/test",
                json=guest_data,
                timeout=10,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Guest addition test passed!")
                print(f"   Response: {result.get('response', '')[:100]}...")
            else:
                print(f"❌ Guest addition failed: {response.status_code}")
                
        else:
            print(f"❌ SMS test failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ SMS test error: {e}")
        return False
    
    print(f"\n🎉 App deployment test completed!")
    print(f"\n📱 To test with real SMS:")
    print(f"   1. Configure Twilio webhook: {base_url}/sms/webhook")
    print(f"   2. Send SMS to your Twilio number")
    print(f"   3. Follow the complete workflow!")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_deployed_app.py https://your-app.railway.app")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    success = test_deployed_app(base_url)
    
    if not success:
        sys.exit(1)
