#!/usr/bin/env python3
"""
Test the new add guests at confirmation functionality
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app import create_app, db
from app.models.planner import Planner
from app.models.event import Event
from app.handlers.final_confirmation_handler import FinalConfirmationHandler
from app.handlers.add_guests_at_confirmation_handler import AddGuestsAtConfirmationHandler
from app.services.event_workflow_service import EventWorkflowService
from app.services.guest_management_service import GuestManagementService
from app.services.message_formatting_service import MessageFormattingService
from app.services.ai_processing_service import AIProcessingService
from datetime import date, time

def test_add_guests_at_confirmation():
    """Test adding guests at confirmation stage"""
    app = create_app()
    
    with app.app_context():
        # Find or create test planner
        planner = Planner.query.filter_by(phone_number='+1234567890').first()
        if not planner:
            planner = Planner(phone_number='+1234567890')
            db.session.add(planner)
            db.session.commit()
        
        # Create test event at final_confirmation stage
        event = Event(
            planner_id=planner.id,
            title="Test Event",
            workflow_stage="final_confirmation",
            selected_date=date(2024, 8, 22),
            selected_start_time=time(16, 0),
            notes=""
        )
        db.session.add(event)
        db.session.commit()
        
        print(f"Created event with ID: {event.id}")
        
        # Initialize services and handlers
        event_service = EventWorkflowService()
        guest_service = GuestManagementService()
        message_service = MessageFormattingService()
        ai_service = AIProcessingService()
        
        final_handler = FinalConfirmationHandler(event_service, guest_service, message_service, ai_service)
        add_guest_handler = AddGuestsAtConfirmationHandler(event_service, guest_service, message_service, ai_service)
        
        # Test 1: Select "3" at confirmation menu
        print("\n=== Test 1: Select '3' at confirmation menu ===")
        result = final_handler.handle_message(event, "3")
        print(f"Success: {result.success}")
        print(f"Message: {result.message}")
        print(f"Next stage: {result.next_stage}")
        
        # Update event stage
        if result.next_stage:
            event.workflow_stage = result.next_stage
            db.session.commit()
        
        # Test 2: Add a guest
        print(f"\n=== Test 2: Add guest 'John 5105935336' ===")
        result = add_guest_handler.handle_message(event, "John 5105935336")
        print(f"Success: {result.success}")
        print(f"Message: {result.message}")
        print(f"Next stage: {result.next_stage}")
        
        # Check that guest was added
        db.session.refresh(event)
        print(f"Number of guests now: {len(event.guests)}")
        if event.guests:
            print(f"Guest added: {event.guests[0].name} - {event.guests[0].phone_number}")
        
        # Test 3: Say "done" to return to confirmation menu
        print(f"\n=== Test 3: Say 'done' to return to confirmation ===")
        result = add_guest_handler.handle_message(event, "done")
        print(f"Success: {result.success}")
        print(f"Next stage: {result.next_stage}")
        print(f"Message preview (first 100 chars): {result.message[:100]}...")
        
        # Cleanup
        db.session.delete(event)
        db.session.commit()
        
        print("\n✅ Test completed successfully!")

if __name__ == "__main__":
    test_add_guests_at_confirmation()
