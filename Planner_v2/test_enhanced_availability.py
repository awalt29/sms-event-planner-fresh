#!/usr/bin/env python3
"""Test the enhanced availability collection system"""

from app import create_app
from app.handlers.availability_tracking_handler import AvailabilityTrackingHandler
from app.handlers.partial_time_selection_handler import PartialTimeSelectionHandler
from app.models.event import Event
from app.models.planner import Planner
from app.models.guest import Guest
from app.services.event_workflow_service import EventWorkflowService
from app.services.guest_management_service import GuestManagementService
from app.services.message_formatting_service import MessageFormattingService
from app.services.ai_processing_service import AIProcessingService

app = create_app()

def test_enhanced_availability():
    with app.app_context():
        # Clean up any existing test data
        test_planner = Planner.query.filter_by(phone_number="+12345678901").first()
        if test_planner:
            # Delete events and guests
            for event in test_planner.events:
                for guest in event.guests:
                    guest.delete()
                event.delete()
            test_planner.delete()
        
        # Create test planner and event
        test_planner = Planner(phone_number="+12345678901", name="Test Planner")
        test_planner.save()
        
        test_event = Event(
            planner_id=test_planner.id,
            workflow_stage='collecting_availability',
            notes="Test event with partial responses"
        )
        test_event.save()
        
        # Create test guests - 3 with availability, 2 without
        guests = [
            Guest(event_id=test_event.id, name="John", phone_number="+15105935331", availability_provided=True),
            Guest(event_id=test_event.id, name="Mary", phone_number="+15105935332", availability_provided=True), 
            Guest(event_id=test_event.id, name="Mike", phone_number="+15105935333", availability_provided=True),
            Guest(event_id=test_event.id, name="Sarah", phone_number="+15105935334", availability_provided=False),
            Guest(event_id=test_event.id, name="Tom", phone_number="+15105935335", availability_provided=False)
        ]
        
        for guest in guests:
            guest.save()
        
        # Initialize services and handlers
        event_service = EventWorkflowService()
        guest_service = GuestManagementService()
        message_service = MessageFormattingService()
        ai_service = AIProcessingService()
        
        availability_handler = AvailabilityTrackingHandler(event_service, guest_service, message_service, ai_service)
        partial_time_handler = PartialTimeSelectionHandler(event_service, guest_service, message_service, ai_service)
        
        print("=== Testing Enhanced Availability Collection ===\n")
        
        # Test 1: Status message with partial responses
        print("1. Testing status with partial responses:")
        status_result = availability_handler.handle_message(test_event, "status")
        print(f"Success: {status_result.success}")
        print(f"Message:\n{status_result.message}\n")
        
        # Test 2: Request partial overlaps with "1"
        print("2. Testing partial overlap request:")
        overlap_result = availability_handler.handle_message(test_event, "1")
        print(f"Success: {overlap_result.success}")
        print(f"New stage: {overlap_result.next_stage}")
        print(f"Message:\n{overlap_result.message}\n")
        
        # Test 3: Late arrival scenario
        print("3. Testing late arrival scenario:")
        # Simulate planner moving to venue selection
        test_event.workflow_stage = 'collecting_activity'
        test_event.save()
        
        # Simulate late guest (Sarah) providing availability
        sarah = guests[3]  # Sarah
        sarah.availability_provided = True
        sarah.save()
        
        # Check if this triggers the late arrival logic
        print(f"Event stage before late arrival: {test_event.workflow_stage}")
        
        # Simulate late arrival notification (this would normally happen through guest availability handler)
        from app.handlers.guest_availability_handler import GuestAvailabilityHandler
        guest_handler = GuestAvailabilityHandler(event_service, guest_service, message_service, ai_service)
        
        # Create a mock guest state for testing
        from app.models.guest_state import GuestState
        mock_guest_state = GuestState(
            phone_number=sarah.phone_number,
            event_id=test_event.id,
            current_state='providing_availability',
            state_data='{"step": "completed"}'
        )
        mock_guest_state.save()
        
        # Test the late arrival notification
        try:
            notification_response = guest_handler._handle_send_availability(mock_guest_state)
            print(f"Notification sent: {notification_response}")
            
            # Check if event was forced back to availability stage
            test_event = Event.query.get(test_event.id)  # Refresh from DB
            print(f"Event stage after late arrival: {test_event.workflow_stage}")
            
        except Exception as e:
            print(f"Error testing late arrival: {e}")
        
        # Cleanup
        mock_guest_state.delete()
        for guest in guests:
            guest.delete()
        test_event.delete()
        test_planner.delete()
        
        print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_enhanced_availability()
