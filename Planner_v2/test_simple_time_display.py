#!/usr/bin/env python3
"""
Simple test to verify start time functionality is working
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app import create_app, db
from app.models.planner import Planner
from app.models.event import Event
from app.services.message_formatting_service import MessageFormattingService
from datetime import date, time

def test_time_display():
    """Test that time display works correctly with notes-based tracking"""
    app = create_app()
    
    with app.app_context():
        # Create event with user-set start time flag in notes
        event = Event(
            title="Test Event",
            selected_date=date(2024, 8, 16),
            selected_start_time=time(16, 0),  # 4pm
            selected_end_time=time(18, 0),    # 6pm
            notes="\nUSER_SET_START_TIME=True"  # This is our flag
        )
        
        formatter = MessageFormattingService()
        confirmation_msg = formatter.format_final_confirmation(event)
        
        # Check that it shows just "4pm" instead of "4pm-6pm"
        if "🕒 Time: 4pm" in confirmation_msg and "4pm-6pm" not in confirmation_msg:
            print("✅ SUCCESS: Time displays as just '4pm' when user sets it")
            print(f"Confirmation message shows: {confirmation_msg.split('🕒 Time: ')[1].split('🏪')[0].strip()}")
        else:
            print("❌ FAILURE: Time display is not working correctly")
            print(f"Full message:\n{confirmation_msg}")
        
        # Test event without USER_SET_START_TIME flag
        event2 = Event(
            title="Test Event 2",
            selected_date=date(2024, 8, 16),
            selected_start_time=time(16, 0),  # 4pm
            selected_end_time=time(18, 0),    # 6pm
            notes=""  # No flag
        )
        
        confirmation_msg2 = formatter.format_final_confirmation(event2)
        
        if "4pm-6pm" in confirmation_msg2:
            print("✅ SUCCESS: Time displays as range '4pm-6pm' when system selects it")
            print(f"Confirmation message shows: {confirmation_msg2.split('🕒 Time: ')[1].split('🏪')[0].strip()}")
        else:
            print("❌ FAILURE: Range display is not working correctly")
            print(f"Full message:\n{confirmation_msg2}")

if __name__ == "__main__":
    test_time_display()
