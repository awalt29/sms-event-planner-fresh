#!/usr/bin/env python3
"""Test Saturday specifically to debug the backward date issue"""

from app import create_app
from app.handlers.date_collection_handler import DateCollectionHandler
from app.models.event import Event
from app.models.planner import Planner
from app.services.event_workflow_service import EventWorkflowService
from app.services.guest_management_service import GuestManagementService
from app.services.message_formatting_service import MessageFormattingService
from app.services.ai_processing_service import AIProcessingService

app = create_app()

def test_saturday_handler():
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
        
        print("=== Testing Saturday parsing ===")
        
        # Test direct parsing methods
        print("\n1. Testing _looks_like_date_input:")
        looks_like_date = handler._looks_like_date_input("Saturday")
        print(f"'Saturday' looks like date: {looks_like_date}")
        
        print("\n2. Testing AI parsing:")
        ai_result = handler._ai_parse_dates("Saturday")
        print(f"AI result: {ai_result}")
        
        print("\n3. Testing simple parsing:")
        simple_result = handler._simple_parse_dates("Saturday")
        print(f"Simple result: {simple_result}")
        
        print("\n4. Testing main parsing:")
        main_result = handler._parse_date_input("Saturday")
        print(f"Main result: {main_result}")
        
        print("\n5. Testing full handler:")
        handler_result = handler.handle_message(test_event, "Saturday")
        print(f"Handler success: {handler_result.success}")
        print(f"Handler message: {handler_result.message}")

if __name__ == "__main__":
    test_saturday_handler()
