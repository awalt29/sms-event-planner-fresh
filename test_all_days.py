#!/usr/bin/env python3

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.handlers.guest_availability_handler import GuestAvailabilityHandler
from app.services.event_workflow_service import EventWorkflowService
from app.services.guest_management_service import GuestManagementService
from app.services.message_formatting_service import MessageFormattingService
from app.services.ai_processing_service import AIProcessingService
from app import create_app
from datetime import datetime, timedelta

def test_all_day_availability():
    """Test that all day names correctly match event dates"""
    
    # Create app and handler with proper services
    app = create_app()
    
    with app.app_context():
        # Initialize services
        event_service = EventWorkflowService()
        guest_service = GuestManagementService()
        message_service = MessageFormattingService()
        ai_service = AIProcessingService()
        
        handler = GuestAvailabilityHandler(event_service, guest_service, message_service, ai_service)
        
        # Simulate the event dates from the screenshot
        context = {
            'event_dates': [
                '2025-08-25',  # Monday, August 25
                '2025-08-26',  # Tuesday, August 26  
                '2025-08-27',  # Wednesday, August 27
                '2025-08-28',  # Thursday, August 28
                '2025-08-29',  # Friday, August 29
                '2025-08-30'   # Saturday, August 30
            ]
        }
        
        # Test cases for all days
        test_cases = [
            ("Monday after 2pm", "2025-08-25", "Monday"),
            ("Tuesday morning", "2025-08-26", "Tuesday"),
            ("Wednesday afternoon", "2025-08-27", "Wednesday"), 
            ("Thursday evening", "2025-08-28", "Thursday"),
            ("Friday all day", "2025-08-29", "Friday"),
            ("Saturday after 3pm", "2025-08-30", "Saturday")
        ]
        
        print("Testing all day name parsing...")
        print("=" * 60)
        print(f"Event dates: {context['event_dates']}")
        print("=" * 60)
        
        all_passed = True
        
        for test_input, expected_date, day_name in test_cases:
            print(f"\n🧪 Testing: '{test_input}'")
            print(f"   Expected date: {expected_date} ({day_name})")
            
            result = handler._ai_parse_availability(test_input, context)
            
            if result and result.get('success'):
                available_dates = result.get('available_dates', [])
                if len(available_dates) > 0:
                    actual_date = available_dates[0].get('date')
                    print(f"   Actual date: {actual_date}")
                    
                    if actual_date == expected_date:
                        print(f"   ✅ PASS: Correctly matched {day_name}!")
                    else:
                        print(f"   ❌ FAIL: Expected {expected_date}, got {actual_date}")
                        all_passed = False
                else:
                    print(f"   ❌ FAIL: No availability entries returned")
                    all_passed = False
            else:
                print(f"   ❌ FAIL: Parsing failed - {result}")
                all_passed = False
        
        print("\n" + "=" * 60)
        if all_passed:
            print("🎉 ALL TESTS PASSED! All day names work correctly!")
        else:
            print("❌ SOME TESTS FAILED! Check the failures above.")
        
        return all_passed

if __name__ == "__main__":
    success = test_all_day_availability()
