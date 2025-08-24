#!/usr/bin/env python3
"""Test the handler message formatting for partial overlaps"""

from app import create_app
from app.models.event import Event
from app.models.planner import Planner
from app.models.guest import Guest
from app.models.availability import Availability
from app.handlers.availability_tracking_handler import AvailabilityTrackingHandler
from app.services.event_workflow_service import EventWorkflowService
from app.services.guest_management_service import GuestManagementService
from app.services.message_formatting_service import MessageFormattingService
from app.services.ai_processing_service import AIProcessingService
from datetime import date, time as dt_time

app = create_app()

def test_handler_time_formatting():
    """Test that handler formats times correctly in partial overlap view"""
    with app.app_context():
        print("🧪 Testing Handler Time Formatting")
        print("=" * 38)
        
        # Clean up
        test_planner = Planner.query.filter_by(phone_number='+19999999997').first()
        if test_planner:
            for event in test_planner.events:
                for guest in event.guests:
                    for avail in guest.availability_records:
                        avail.delete()
                    guest.delete()
                event.delete()
            test_planner.delete()
        
        # Create test data
        planner = Planner(phone_number='+19999999997', name='Test Planner')
        planner.save()
        
        event = Event(
            planner_id=planner.id,
            title='Handler Test',
            workflow_stage='tracking_availability'
        )
        event.save()
        
        # Create guests
        aaron = Guest(
            event_id=event.id,
            name='Aaron',
            phone_number='+15555551111',
            availability_provided=True
        )
        aaron.save()
        
        john = Guest(
            event_id=event.id,
            name='John',
            phone_number='+15555552222',
            availability_provided=False  # Not responded yet
        )
        john.save()
        
        # Add availability
        availability = Availability(
            event_id=event.id,
            guest_id=aaron.id,
            date=date(2025, 8, 29),  # Friday 
            start_time=dt_time(14, 0),  # 2pm
            end_time=dt_time(23, 59),   # 11:59pm
            all_day=False
        )
        availability.save()
        
        print("✅ Created test event:")
        print("   - Aaron: Fri 14:00-23:59 (responded)")
        print("   - John: No response yet")
        
        # Test the handler directly 
        event_service = EventWorkflowService()
        guest_service = GuestManagementService()
        message_service = MessageFormattingService()
        ai_service = AIProcessingService()
        
        handler = AvailabilityTrackingHandler(event_service, guest_service, message_service, ai_service)
        
        # Simulate pressing "1" to view current overlaps
        result = handler._handle_partial_overlap_request(event)
        
        print(f"\n📱 Handler Message Output:")
        print("=" * 40)
        print(result.message)
        print("=" * 40)
        
        # Check for time format
        if "2pm" in result.message:
            print("✅ SUCCESS: Times formatted in 12-hour format (2pm)")
        elif "14:00" in result.message:
            print("❌ FAILED: Times still in military format (14:00)")
        else:
            print("❓ UNCLEAR: No clear time format found")
        
        # Cleanup
        availability.delete()
        aaron.delete()
        john.delete()
        event.delete()
        planner.delete()
        
        print("\n✅ Test complete!")

if __name__ == "__main__":
    test_handler_time_formatting()
