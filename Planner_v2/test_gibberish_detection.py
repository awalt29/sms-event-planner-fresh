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

def test_gibberish_detection():
    """Test that gibberish input is properly rejected"""
    
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
        
        print("Testing gibberish detection...")
        print("=" * 50)
        
        # Test cases that should be REJECTED (gibberish)
        gibberish_cases = [
            "Monday afuiDbdDbeb",  # From the screenshot
            "asdfghjkl",
            "Tuesday xyzabc",
            "qwerty",
            "Monday asldkfjasldkf",
            "xyz123abc",
            "Friday ksjdhfkjshdf"
        ]
        
        # Test cases that should be ACCEPTED (valid)
        valid_cases = [
            "Monday afternoon",
            "Tuesday after 2pm", 
            "Wednesday all day",
            "Thursday morning",
            "Friday 2-6pm",
            "Saturday evening",
            "Monday 9am to 5pm"
        ]
        
        print("Testing GIBBERISH cases (should be rejected):")
        for i, test_input in enumerate(gibberish_cases, 1):
            print(f"  {i}. '{test_input}'")
            
            # Test the validation function directly
            is_valid = handler._is_valid_availability_input(test_input)
            
            if not is_valid:
                print(f"     ✅ CORRECTLY REJECTED as gibberish")
            else:
                # If validation passes, test full parsing
                result = handler._parse_availability_input(test_input, context)
                if result.get('success'):
                    print(f"     ❌ WRONGLY ACCEPTED: {result}")
                else:
                    print(f"     ✅ CORRECTLY REJECTED: {result.get('error')}")
        
        print("\nTesting VALID cases (should be accepted):")
        for i, test_input in enumerate(valid_cases, 1):
            print(f"  {i}. '{test_input}'")
            
            is_valid = handler._is_valid_availability_input(test_input)
            
            if is_valid:
                print(f"     ✅ CORRECTLY ACCEPTED as valid")
            else:
                print(f"     ❌ WRONGLY REJECTED as gibberish")

if __name__ == "__main__":
    test_gibberish_detection()
