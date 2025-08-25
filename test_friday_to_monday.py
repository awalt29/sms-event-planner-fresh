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

def test_friday_to_monday():
    """Test that 'Friday to Monday' returns all days in the range"""
    
    app = create_app()
    
    with app.app_context():
        # Initialize services
        event_service = EventWorkflowService()
        guest_service = GuestManagementService()
        message_service = MessageFormattingService()
        ai_service = AIProcessingService()
        
        handler = DateCollectionHandler(event_service, guest_service, message_service, ai_service)
        
        # Test input that's failing
        test_input = "Friday to Monday"
        
        print(f"Testing: '{test_input}'")
        print("=" * 50)
        
        # Test AI parsing directly
        print("AI Parsing Result:")
        ai_result = handler._ai_parse_dates(test_input)
        print(f"AI Result: {ai_result}")
        
        # Test backup parsing directly
        print("\nBackup Parsing Result:")
        backup_result = handler._simple_parse_dates(test_input)
        print(f"Backup Result: {backup_result}")
        
        # Test combined parsing
        print("\nCombined Parsing Result:")
        combined_result = handler._parse_date_input(test_input)
        print(f"Combined Result: {combined_result}")
        
        if combined_result.get('success'):
            dates = combined_result.get('dates', [])
            print(f"\nNumber of dates returned: {len(dates)}")
            print(f"Dates: {dates}")
            print(f"Dates text: {combined_result.get('dates_text')}")
            
            # We should get Friday (15th), Saturday (16th), Sunday (17th), Monday (18th) = 4 days
            expected_count = 4
            if len(dates) == expected_count:
                print(f"✅ SUCCESS: Got all {expected_count} days!")
                
                # Verify the actual days
                for date_str in dates:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    weekday = date_obj.strftime('%A')
                    print(f"  - {date_str} is a {weekday}")
                    
                return True
            else:
                print(f"❌ FAILED: Expected {expected_count} dates, got {len(dates)}")
                return False
        else:
            print(f"❌ FAILED: Parsing failed - {combined_result}")
            return False

if __name__ == "__main__":
    test_friday_to_monday()
