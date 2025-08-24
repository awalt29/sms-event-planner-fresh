#!/usr/bin/env python3

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.handlers.date_collection_handler import DateCollectionHandler
from app.services.event_workflow_service import EventWorkflowService
from app.services.guest_management_service import GuestManagementService
from app.services.message_formatting_service import MessageFormattingService
from app.services.ai_processing_service import AIProcessingService
from app import create_app
from datetime import datetime, timedelta

def test_friday_or_saturday():
    """Test that 'Friday or Saturday' returns both days"""
    
    # Create app and handler with proper services
    app = create_app()
    
    with app.app_context():
        # Initialize services
        event_service = EventWorkflowService()
        guest_service = GuestManagementService()
        message_service = MessageFormattingService()
        ai_service = AIProcessingService()
        
        handler = DateCollectionHandler(event_service, guest_service, message_service, ai_service)
        
        # Test input that was failing
        test_input = "Friday or Saturday"
        result = handler._parse_date_input(test_input)
        
        print(f"Input: '{test_input}'")
        print(f"Result: {result}")
        
        # Verify we got both days
        if result.get('success'):
            dates = result.get('dates', [])
            print(f"Number of dates returned: {len(dates)}")
            print(f"Dates: {dates}")
            print(f"Dates text: {result.get('dates_text')}")
            
            # We should get exactly 2 dates
            if len(dates) == 2:
                print("✅ SUCCESS: Got both Friday and Saturday!")
                
                # Verify they are Friday and Saturday
                for date_str in dates:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    weekday = date_obj.strftime('%A')
                    print(f"  - {date_str} is a {weekday}")
                    
                return True
            else:
                print(f"❌ FAILED: Expected 2 dates, got {len(dates)}")
                return False
        else:
            print(f"❌ FAILED: Parsing failed - {result}")
            return False

def test_various_combinations():
    """Test various day combinations"""
    
    app = create_app()
    
    with app.app_context():
        # Initialize services
        event_service = EventWorkflowService()
        guest_service = GuestManagementService()
        message_service = MessageFormattingService()
        ai_service = AIProcessingService()
        
        handler = DateCollectionHandler(event_service, guest_service, message_service, ai_service)
        
        test_cases = [
            "Friday or Saturday",
            "Friday and Saturday", 
            "Saturday or Friday",
            "Saturday and Friday",
            "Tuesday or Wednesday",
            "Tuesday and Wednesday"
        ]
        
        for test_input in test_cases:
            print(f"\n--- Testing: '{test_input}' ---")
            result = handler._parse_date_input(test_input)
            
            if result.get('success'):
                dates = result.get('dates', [])
                print(f"✅ Got {len(dates)} dates: {result.get('dates_text')}")
            else:
                print(f"❌ Failed: {result}")

if __name__ == "__main__":
    print("Testing Friday or Saturday parsing...")
    print("=" * 50)
    
    success = test_friday_or_saturday()
    
    print("\n" + "=" * 50)
    print("Testing various combinations...")
    test_various_combinations()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Main test PASSED!")
    else:
        print("❌ Main test FAILED!")
