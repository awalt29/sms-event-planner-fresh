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

def test_user_experience():
    """Test what the user sees when they send gibberish vs valid input"""
    
    app = create_app()
    
    with app.app_context():
        # Initialize services
        event_service = EventWorkflowService()
        guest_service = GuestManagementService()
        message_service = MessageFormattingService()
        ai_service = AIProcessingService()
        
        handler = GuestAvailabilityHandler(event_service, guest_service, message_service, ai_service)
        
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
        
        print("User Experience Test")
        print("=" * 50)
        
        # Test the exact gibberish from the screenshot
        gibberish_input = "Monday afuiDbdDbeb"
        print(f"User sends: '{gibberish_input}'")
        print("-" * 30)
        
        result = handler._parse_availability_input(gibberish_input, context)
        
        if result.get('success'):
            print("❌ PROBLEM: System accepted gibberish!")
            print(f"System would respond: {result}")
        else:
            print("✅ GOOD: System rejected gibberish!")
            print(f"User sees error: '{result.get('error')}'")
        
        print("\n" + "=" * 50)
        
        # Test valid input for comparison
        valid_input = "Monday afternoon"
        print(f"User sends: '{valid_input}'")
        print("-" * 30)
        
        result2 = handler._parse_availability_input(valid_input, context)
        
        if result2.get('success'):
            print("✅ GOOD: System accepted valid input!")
            avail = result2['available_dates'][0]
            print(f"Parsed as: {avail['date']} from {avail['start_time']} to {avail['end_time']}")
        else:
            print("❌ PROBLEM: System rejected valid input!")
            print(f"Error: {result2.get('error')}")

if __name__ == "__main__":
    test_user_experience()
