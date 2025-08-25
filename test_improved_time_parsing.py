#!/usr/bin/env python3

import os
import sys
sys.path.append('/Users/aaronwalters/Planner_app_live/Planner_v2')

from app import create_app
from app.handlers.guest_availability_handler import GuestAvailabilityHandler
from app.services.event_workflow_service import EventWorkflowService
from app.services.guest_management_service import GuestManagementService
from app.services.message_formatting_service import MessageFormattingService
from app.services.ai_processing_service import AIProcessingService

def test_improved_time_parsing():
    app = create_app()
    
    with app.app_context():
        print("🧪 Testing Improved Time Parsing")
        print("=" * 40)
        
        # Initialize handler
        event_service = EventWorkflowService()
        guest_service = GuestManagementService()
        message_service = MessageFormattingService()
        ai_service = AIProcessingService()
        
        handler = GuestAvailabilityHandler(
            event_service, guest_service, message_service, ai_service
        )
        
        # Test cases for shorthand time parsing
        test_cases = [
            ("Friday 7-11p", "Friday 7pm-11pm"),
            ("Saturday 11-5", "Saturday 11am-5pm"),
            ("Friday 7-11p, Saturday 11-5", "Friday 7pm-11pm AND Saturday 11am-5pm"),
            ("Friday 2-6pm", "Friday 2pm-6pm"),
            ("Saturday 9a-12p", "Saturday 9am-12pm"),
            ("Friday after 7p", "Friday after 7pm"),
            ("Saturday all day", "Saturday all day"),
            ("Friday evening", "Friday evening"),
        ]
        
        context = {
            'event_dates': ['2025-08-15', '2025-08-16']  # Friday, Saturday
        }
        
        for test_input, description in test_cases:
            print(f"\n📝 Testing: '{test_input}' ({description})")
            print("-" * 50)
            
            # Test simple parsing first
            simple_result = handler._simple_parse_availability(test_input)
            print(f"Simple Parser Result:")
            if simple_result and simple_result.get('success'):
                for avail in simple_result.get('available_dates', []):
                    print(f"  ✅ {avail['date']}: {avail['start_time']}-{avail['end_time']}")
            else:
                print(f"  ❌ Failed: {simple_result}")
            
            # Test AI parsing (this might take longer)
            print(f"AI Parser Result:")
            try:
                ai_result = handler._ai_parse_availability(test_input, context)
                if ai_result and ai_result.get('success'):
                    for avail in ai_result.get('available_dates', []):
                        print(f"  ✅ {avail['date']}: {avail['start_time']}-{avail['end_time']}")
                else:
                    print(f"  ❌ Failed: {ai_result}")
            except Exception as e:
                print(f"  ❌ AI Error: {e}")
        
        # Test specific shorthand time parsing method
        print(f"\n🔧 Testing Shorthand Time Parser:")
        print("-" * 35)
        
        shorthand_tests = [
            "7-11p",
            "11-5", 
            "2-6pm",
            "9a-12p",
            "7p",
            "11a"
        ]
        
        for shorthand in shorthand_tests:
            result = handler._parse_shorthand_time(shorthand)
            if result:
                print(f"  '{shorthand}' → {result['start']}-{result['end']}")
            else:
                print(f"  '{shorthand}' → No match")
        
        print(f"\n✅ Time parsing test complete!")

if __name__ == "__main__":
    test_improved_time_parsing()
