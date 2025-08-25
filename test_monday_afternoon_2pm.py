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

def test_monday_afternoon_2pm():
    """Test the exact input from the screenshot that caused issues"""
    
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
        
        # Test the exact problematic input
        test_input = "Monday afternoon 2pm"
        
        print(f"Testing: '{test_input}'")
        print("=" * 50)
        
        result = handler._ai_parse_availability(test_input, context)
        print(f"AI parsing result: {result}")
        
        if result and result.get('success'):
            available_dates = result.get('available_dates', [])
            if len(available_dates) > 0:
                avail = available_dates[0]
                date = avail.get('date')
                start_time = avail.get('start_time')
                end_time = avail.get('end_time')
                
                print(f"\nParsed result:")
                print(f"  Date: {date}")
                print(f"  Start time: {start_time}")
                print(f"  End time: {end_time}")
                
                # Test validation
                validation = handler._validate_availability_entry(avail)
                print(f"\nValidation result:")
                if validation['valid']:
                    print(f"  ✅ VALID: Time range is acceptable")
                    
                    # Calculate duration
                    from datetime import datetime
                    start_dt = datetime.strptime(start_time, '%H:%M')
                    end_dt = datetime.strptime(end_time, '%H:%M')
                    duration = (end_dt - start_dt).total_seconds() / 3600  # hours
                    print(f"  Duration: {duration} hours")
                    
                else:
                    print(f"  ❌ INVALID: {validation['error']}")
                    print(f"  System would ask user to clarify")
            else:
                print("❌ No availability entries returned")
        else:
            print(f"❌ AI parsing failed: {result}")

if __name__ == "__main__":
    test_monday_afternoon_2pm()
