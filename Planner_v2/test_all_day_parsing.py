#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.handlers.guest_availability_handler import GuestAvailabilityHandler
from app.services import EventWorkflowService, GuestManagementService, MessageFormattingService, AIProcessingService

def test_all_day_parsing():
    """Test that 'all day' is now parsed as 'after 8am' (08:00-23:59)"""
    
    # Initialize handler
    handler = GuestAvailabilityHandler(
        event_service=EventWorkflowService(),
        guest_service=GuestManagementService(),
        message_service=MessageFormattingService(),
        ai_service=AIProcessingService()
    )
    
    test_inputs = [
        "Friday all day",
        "Saturday all day", 
        "Monday all day"
    ]
    
    context = {
        'event_dates': ['2025-08-15', '2025-08-16', '2025-08-18']  # Friday, Saturday, Monday
    }
    
    print("🕰️ Testing 'All Day' Parsing Update")
    print("Expected: 'all day' should be 08:00-23:59 (after 8am)")
    print("=" * 60)
    
    for test_input in test_inputs:
        print(f"\n📝 Testing: '{test_input}'")
        print("-" * 40)
        
        # Test simple parsing
        simple_result = handler._simple_parse_availability(test_input)
        print(f"Simple Parser:")
        if simple_result and simple_result.get('success'):
            for avail in simple_result.get('available_dates', []):
                start_time = avail['start_time']
                end_time = avail['end_time']
                all_day = avail.get('all_day', False)
                print(f"  ✅ {avail['date']}: {start_time}-{end_time} (all_day: {all_day})")
                
                # Validate it's the new format
                if start_time == '08:00' and end_time == '23:59':
                    print(f"  ✅ Correct: Now treated as 'after 8am'")
                elif start_time == '09:00' and end_time == '17:00':
                    print(f"  ❌ Old format: Still using 9am-5pm")
                else:
                    print(f"  ⚠️  Unexpected format: {start_time}-{end_time}")
        else:
            print(f"  ❌ Failed: {simple_result}")
        
        # Test AI parsing 
        ai_result = handler._ai_parse_availability(test_input, context)
        print(f"AI Parser:")
        if ai_result and ai_result.get('success'):
            for avail in ai_result.get('available_dates', []):
                start_time = avail['start_time']
                end_time = avail['end_time']
                all_day = avail.get('all_day', False)
                print(f"  ✅ {avail['date']}: {start_time}-{end_time} (all_day: {all_day})")
                
                # Validate it's the new format
                if start_time == '08:00' and end_time == '23:59':
                    print(f"  ✅ Correct: AI also treats as 'after 8am'")
                elif start_time == '09:00' and end_time == '17:00':
                    print(f"  ❌ Old format: AI still using 9am-5pm")
                else:
                    print(f"  ⚠️  Unexpected format: {start_time}-{end_time}")
        else:
            print(f"  ❌ Failed: {ai_result}")

if __name__ == "__main__":
    test_all_day_parsing()
