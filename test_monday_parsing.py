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

def test_monday_availability():
    """Test that 'Monday after 2pm' matches the correct Monday from event dates"""
    
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
        
        # Test input that was failing
        test_input = "Monday after 2pm"
        
        print(f"Input: '{test_input}'")
        print(f"Event dates: {context['event_dates']}")
        
        # Check if AI service has API key
        if not ai_service.api_key:
            print("❌ No OpenAI API key found - AI parsing will fail")
            print("Set OPENAI_API_KEY environment variable")
            return False
        
        result = handler._ai_parse_availability(test_input, context)
        print(f"Result: {result}")
        
        # Verify we got the correct Monday
        if result and result.get('success'):
            available_dates = result.get('available_dates', [])
            print(f"Number of availability entries: {len(available_dates)}")
            
            if len(available_dates) > 0:
                avail = available_dates[0]
                date = avail.get('date')
                start_time = avail.get('start_time')
                end_time = avail.get('end_time')
                
                print(f"Parsed date: {date}")
                print(f"Start time: {start_time}")
                print(f"End time: {end_time}")
                
                # Check if it's Monday August 25th (correct) vs August 18th (wrong)
                if date == '2025-08-25':
                    print("✅ SUCCESS: Correctly matched Monday, August 25th!")
                    return True
                elif date == '2025-08-18':
                    print("❌ FAILED: Still using wrong Monday (August 18th)")
                    return False
                else:
                    print(f"❌ FAILED: Unexpected date {date}")
                    return False
            else:
                print("❌ FAILED: No availability entries returned")
                return False
        else:
            print(f"❌ FAILED: Parsing failed - {result}")
            return False

if __name__ == "__main__":
    print("Testing Monday availability parsing...")
    print("=" * 50)
    
    success = test_monday_availability()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Test PASSED! Monday parsing is fixed!")
    else:
        print("❌ Test FAILED! Monday parsing still broken.")
