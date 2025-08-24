#!/usr/bin/env python3
"""Test the full date collection handler workflow"""

from app import create_app
from app.handlers.date_collection_handler import DateCollectionHandler
from app.models.event import Event
from app.models.planner import Planner
from app.services.event_workflow_service import EventWorkflowService
from app.services.guest_management_service import GuestManagementService
from app.services.message_formatting_service import MessageFormattingService
from app.services.ai_processing_service import AIProcessingService

app = create_app()

def test_full_handler():
    with app.app_context():
        # Create a test planner and event
        test_planner = Planner.query.first()
        if not test_planner:
            test_planner = Planner(phone_number="+12345678901", name="Test Planner")
            test_planner.save()
            
        test_event = Event.query.filter_by(planner_id=test_planner.id).first()
        if test_event:
            test_event.delete()
            
        test_event = Event(
            planner_id=test_planner.id,
            workflow_stage='collecting_dates',
            notes=""
        )
        test_event.save()
        
        # Initialize services
        event_service = EventWorkflowService()
        guest_service = GuestManagementService()
        message_service = MessageFormattingService()
        ai_service = AIProcessingService()
        
        # Test the date handler
        handler = DateCollectionHandler(event_service, guest_service, message_service, ai_service)
        
        # Test the full handle_message method
        test_cases = ["Friday"]
        
        for test_input in test_cases:
            print(f"\n--- Testing full handler: '{test_input}' ---")
            
            result = handler.handle_message(test_event, test_input)
            print(f"Handler result: {result}")
            print(f"Success: {result.success}")
            print(f"Message: {result.message}")
            print(f"Next stage: {result.next_stage if hasattr(result, 'next_stage') else 'No next_stage attr'}")
            print(f"Event notes after: {test_event.notes}")

if __name__ == "__main__":
    test_full_handler()
