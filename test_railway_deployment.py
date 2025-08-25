#!/usr/bin/env python3
"""
Test script to verify Railway deployment works
"""
import requests
import sys

def test_railway_deployment():
    """Test that Railway is running the latest code"""
    try:
        # Test health endpoint
        health_response = requests.get("https://web-production-faa49.up.railway.app/health")
        print(f"Health check: {health_response.status_code}")
        print(f"Health response: {health_response.json()}")
        
        # Test SMS endpoint with simple message
        sms_data = {
            "From": "+15551234567",
            "To": "+15559876543", 
            "Body": "test message"
        }
        sms_response = requests.post(
            "https://web-production-faa49.up.railway.app/sms/webhook",
            data=sms_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        print(f"SMS test: {sms_response.status_code}")
        print(f"SMS response: {sms_response.text}")
        
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_railway_deployment()
