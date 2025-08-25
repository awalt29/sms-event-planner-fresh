#!/usr/bin/env python3
"""
Performance Test for SMS Router Optimizations

Tests the performance improvements from:
1. Removed data integrity blocking
2. Singleton services 
3. Reduced AI timeouts

Usage: python performance_test_sms.py
"""

import os
import sys
import time
import statistics
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.routes.sms import SMSRouter

def time_router_creation(iterations=10):
    """Test how long it takes to create SMSRouter instances"""
    print(f"🧪 Testing SMSRouter creation ({iterations} iterations)")
    
    times = []
    for i in range(iterations):
        start = time.time()
        router = SMSRouter()
        end = time.time()
        
        duration = end - start
        times.append(duration)
        print(f"  Creation {i+1}: {duration:.4f}s")
    
    avg = statistics.mean(times)
    median = statistics.median(times)
    print(f"  Average: {avg:.4f}s")
    print(f"  Median: {median:.4f}s")
    print(f"  Best: {min(times):.4f}s")
    print(f"  Worst: {max(times):.4f}s")
    
    return avg

def test_service_reuse():
    """Test that services are actually being reused"""
    print(f"\n🔧 Testing service reuse")
    
    router1 = SMSRouter()
    router2 = SMSRouter()
    
    same_instances = (
        router1.event_service is router2.event_service and
        router1.ai_service is router2.ai_service and
        router1.guest_service is router2.guest_service
    )
    
    print(f"  Same service instances: {'✅ YES' if same_instances else '❌ NO'}")
    print(f"  EventService ID: {id(router1.event_service)} vs {id(router2.event_service)}")
    print(f"  AIService ID: {id(router1.ai_service)} vs {id(router2.ai_service)}")
    
    return same_instances

def simulate_sms_load(num_messages=5):
    """Simulate multiple SMS messages to test performance"""
    print(f"\n📱 Simulating {num_messages} SMS messages")
    
    app = create_app()
    
    with app.app_context():
        router = SMSRouter()
        
        test_messages = [
            ("5551234567", "Hi"),
            ("5551234567", "reset"),  
            ("5551234567", "Aaron(9145606464)"),
            ("5551234567", "Friday 7pm"),
            ("5551234567", "status")
        ]
        
        times = []
        
        for i, (phone, message) in enumerate(test_messages[:num_messages]):
            print(f"  Message {i+1}: '{message}'")
            
            start = time.time()
            try:
                response = router.route_message(phone, message)
                end = time.time()
                
                duration = end - start
                times.append(duration)
                
                print(f"    Processed in: {duration:.4f}s")
                print(f"    Response length: {len(response)} chars")
                
            except Exception as e:
                print(f"    ❌ Error: {e}")
        
        if times:
            avg = statistics.mean(times)
            print(f"\n  Average processing time: {avg:.4f}s")
            print(f"  Fastest: {min(times):.4f}s")
            print(f"  Slowest: {max(times):.4f}s")
            
            return avg
        else:
            return None

def main():
    """Run all performance tests"""
    print("🚀 SMS Router Performance Test")
    print("=" * 50)
    print(f"Test started: {datetime.now()}")
    
    try:
        # Test 1: Router creation speed
        creation_time = time_router_creation(5)
        
        # Test 2: Service reuse
        services_reused = test_service_reuse()
        
        # Test 3: Message processing
        processing_time = simulate_sms_load(5)
        
        # Summary
        print(f"\n📊 Performance Summary")
        print("=" * 30)
        print(f"Router creation: {creation_time:.4f}s avg")
        print(f"Services reused: {'✅' if services_reused else '❌'}")
        
        if processing_time:
            print(f"Message processing: {processing_time:.4f}s avg")
            
            # Performance assessment
            if processing_time < 0.1:
                print("🎉 EXCELLENT: Sub-100ms processing!")
            elif processing_time < 0.3:
                print("✅ GOOD: Sub-300ms processing")
            elif processing_time < 0.5:
                print("⚠️ OK: Sub-500ms processing")
            else:
                print("❌ SLOW: Over 500ms - needs more optimization")
        
        print(f"\nTest completed: {datetime.now()}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
