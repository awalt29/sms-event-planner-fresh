#!/usr/bin/env python3
"""Test the date parsing functionality"""

from app import create_app
from app.handlers.date_collection_handler import DateCollectionHandler
from app.models.event import Event
from app.models.planner import Planner
from app.services.event_workflow_service import EventWorkflowService
from app.services.guest_management_service import GuestManagementService
from app.services.message_formatting_service import MessageFormattingService
from app.services.ai_processing_service import AIProcessingService

app = create_app()

def test_date_parsing():
    with app.app_context():
        # Create a test planner and event
        test_planner = Planner.query.first()
        if not test_planner:
            test_planner = Planner(phone_number="+12345678901", name="Test Planner")
            test_planner.save()
            
        test_event = Event.query.first()
        if not test_event:
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
        
        # Test cases from the screenshots
        test_cases = [
            "Friday",
            "Friday or Saturday", 
            "Next Friday or Saturday",
            "Saturday and Sunday"
        ]
        
        for test_input in test_cases:
            print(f"\n--- Testing: '{test_input}' ---")
            
            # Test if it looks like date input
            looks_like_date = handler._looks_like_date_input(test_input)
            print(f"Looks like date input: {looks_like_date}")
            
            if looks_like_date:
                # Test AI parsing
                ai_result = handler._ai_parse_dates(test_input)
                print(f"AI parsing result: {ai_result}")
                
                # Test simple parsing fallback
                simple_result = handler._simple_parse_dates(test_input)
                print(f"Simple parsing result: {simple_result}")
                
                # Test the main parsing function
                main_result = handler._parse_date_input(test_input)
                print(f"Main parsing result: {main_result}")
            else:
                print("Input rejected - doesn't look like date input")

if __name__ == "__main__":
    test_date_parsing()
