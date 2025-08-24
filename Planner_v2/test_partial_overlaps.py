#!/usr/bin/env python3
"""Test partial overlaps with real availability data"""

from app import create_app
from app.handlers.availability_tracking_handler import AvailabilityTrackingHandler
from app.models.event import Event
from app.models.planner import Planner
from app.models.guest import Guest
from app.models.availability import Availability
from app.services.event_workflow_service import EventWorkflowService
from app.services.guest_management_service import GuestManagementService
from app.services.message_formatting_service import MessageFormattingService
from app.services.ai_processing_service import AIProcessingService
from datetime import date, time

app = create_app()

def test_partial_overlaps():
    with app.app_context():
        # Clean up any existing test data
        test_planner = Planner.query.filter_by(phone_number="+12345678901").first()
        if test_planner:
            for event in test_planner.events:
                # Delete availability records
                for guest in event.guests:
                    for avail in guest.availability_records:
                        avail.delete()
                    guest.delete()
                event.delete()
            test_planner.delete()
        
        # Create test planner and event
        test_planner = Planner(phone_number="+12345678901", name="Test Planner")
        test_planner.save()
        
        test_event = Event(
            planner_id=test_planner.id,
            workflow_stage='collecting_availability',
            notes="Test event with real availability data"
        )
        test_event.save()
        
        # Create test guests
        john = Guest(event_id=test_event.id, name="John", phone_number="+15105935331", availability_provided=True)
        mary = Guest(event_id=test_event.id, name="Mary", phone_number="+15105935332", availability_provided=True)
        mike = Guest(event_id=test_event.id, name="Mike", phone_number="+15105935333", availability_provided=True)
        sarah = Guest(event_id=test_event.id, name="Sarah", phone_number="+15105935334", availability_provided=False)
        
        for guest in [john, mary, mike, sarah]:
            guest.save()
        
        # Create overlapping availability data for the 3 responding guests
        test_date = date(2025, 8, 16)  # Saturday
        
        # All three available Saturday 2-4 PM
        for guest in [john, mary, mike]:
            availability = Availability(
                guest_id=guest.id,
                event_id=test_event.id,
                date=test_date,
                start_time=time(14, 0),  # 2 PM
                end_time=time(16, 0),    # 4 PM
                all_day=False
            )
            availability.save()
        
        # Initialize handler
        event_service = EventWorkflowService()
        guest_service = GuestManagementService()
        message_service = MessageFormattingService()
        ai_service = AIProcessingService()
        
        availability_handler = AvailabilityTrackingHandler(event_service, guest_service, message_service, ai_service)
        
        print("=== Testing Partial Overlaps with Real Data ===\n")
        
        # Test partial overlap request
        print("Testing partial overlap request with real availability data:")
        overlap_result = availability_handler.handle_message(test_event, "1")
        print(f"Success: {overlap_result.success}")
        print(f"New stage: {overlap_result.next_stage}")
        print(f"Message:\n{overlap_result.message}\n")
        
        # Cleanup
        for guest in [john, mary, mike, sarah]:
            for avail in guest.availability_records:
                avail.delete()
            guest.delete()
        test_event.delete()
        test_planner.delete()
        
        print("=== Test Complete ===")

if __name__ == "__main__":
    test_partial_overlaps()
