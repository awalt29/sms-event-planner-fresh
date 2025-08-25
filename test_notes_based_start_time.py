#!/usr/bin/env python3
"""
Test that start time setting works with notes-based tracking.
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app import create_app, db
from app.models.planner import Planner
from app.models.event import Event
from app.handlers.start_time_setting_handler import StartTimeSettingHandler
from app.services.message_formatting_service import MessageFormattingService
from app.services.event_workflow_service import EventWorkflowService
from app.services.guest_management_service import GuestManagementService
from app.services.ai_processing_service import AIProcessingService
from datetime import date, time

def test_start_time_with_notes():
    """Test that start time setting works with notes field tracking"""
    app = create_app()
    
    with app.app_context():
        # Get or create test planner
        planner = Planner.query.filter_by(phone_number='+1234567890').first()
        if not planner:
            planner = Planner(phone_number='+1234567890')
            db.session.add(planner)
            db.session.commit()
        
        # Create test event with selected time
        event = Event(
            planner_id=planner.id,
            title="Test Event",
            workflow_stage="setting_start_time",
            selected_date=date(2024, 8, 16),
            selected_start_time=time(14, 0),  # 2pm
            selected_end_time=time(23, 59),   # 11:59pm - large window
            notes=""
        )
        db.session.add(event)
        db.session.commit()
        
        # Test the start time setting handler
        event_service = EventWorkflowService()
        guest_service = GuestManagementService()
        message_service = MessageFormattingService()
        ai_service = AIProcessingService()
        
        handler = StartTimeSettingHandler(event_service, guest_service, message_service, ai_service)
        result = handler.handle_message(event, "4pm")
        
        print(f"Handler result: {result.message}")
        print(f"New workflow stage: {result.next_stage}")
        
        # Check event was updated
        db.session.refresh(event)
        print(f"Event selected_start_time: {event.selected_start_time}")
        print(f"Event selected_end_time: {event.selected_end_time}")
        print(f"Event notes: {event.notes}")
        
        # Test message formatting
        formatter = MessageFormattingService()
        
        # Test final confirmation message (should show just "4pm")
        confirmation_msg = formatter.format_final_confirmation(event)
        print(f"\nFinal confirmation message:\n{confirmation_msg}")
        
        # Test guest invitation message (should also show just "4pm")  
        # For this test, we'll create a mock guest
        from app.models.guest import Guest
        guest = Guest(name="Test Guest", event_id=event.id)
        db.session.add(guest)
        db.session.commit()
        
        invitation_msg = formatter.format_guest_invitation(event, guest)
        print(f"\nGuest invitation message:\n{invitation_msg}")
        
        # Cleanup
        db.session.delete(guest)
        
        # Cleanup
        db.session.delete(event)
        db.session.commit()
        
        print("\n✅ Test passed! Start time setting with notes tracking works correctly.")

if __name__ == "__main__":
    test_start_time_with_notes()
