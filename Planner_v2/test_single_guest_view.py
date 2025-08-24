#!/usr/bin/env python3
"""Test single guest availability display for 'view current overlaps'"""

from app import create_app
from app.models.event import Event
from app.models.planner import Planner
from app.models.guest import Guest
from app.models.availability import Availability
from app.services.availability_service import AvailabilityService
from app.handlers.availability_tracking_handler import AvailabilityTrackingHandler
from app.services.event_workflow_service import EventWorkflowService
from app.services.guest_management_service import GuestManagementService
from app.services.message_formatting_service import MessageFormattingService
from app.services.ai_processing_service import AIProcessingService
from datetime import date, time as dt_time

app = create_app()

def test_single_guest_overlap_view():
    """Test that single guest availability shows up when viewing current overlaps"""
    with app.app_context():
        print("🧪 Testing Single Guest Overlap View")
        print("=" * 45)
        
        # Clean up existing data
        test_planner = Planner.query.filter_by(phone_number='+19999999998').first()
        if test_planner:
            for event in test_planner.events:
                for guest in event.guests:
                    for avail in guest.availability_records:
                        avail.delete()
                    guest.delete()
                event.delete()
            test_planner.delete()
        
        # Create test planner
        planner = Planner(phone_number='+19999999998', name='Test Planner')
        planner.save()
        
        # Create test event
        event = Event(
            planner_id=planner.id,
            title='Single Guest Test',
            workflow_stage='tracking_availability',
            start_date=date(2025, 8, 30)
        )
        event.save()
        
        # Create 2 guests - only 1 will respond
        aaron = Guest(
            event_id=event.id,
            name='Aaron',
            phone_number='+15555551111',
            availability_provided=True,  # This guest responded
            rsvp_status='pending'
        )
        aaron.save()
        
        john = Guest(
            event_id=event.id,
            name='John',
            phone_number='+15555552222',
            availability_provided=False,  # This guest has not responded yet
            rsvp_status='pending'
        )
        john.save()
        
        # Add availability for Aaron only
        aaron_availability = Availability(
            event_id=event.id,
            guest_id=aaron.id,
            date=date(2025, 8, 30),  # Saturday
            start_time=dt_time(14, 0),  # 2pm
            end_time=dt_time(18, 0),    # 6pm
            all_day=False
        )
        aaron_availability.save()
        
        print(f"✅ Created event with:")
        print(f"   - Aaron: Available Sat 2pm-6pm (responded)")
        print(f"   - John: No availability yet (pending)")
        
        # Test 1: Direct service call with show_individual_availability=True
        print(f"\n🔬 Test 1: Direct service call (show_individual=True)")
        availability_service = AvailabilityService()
        overlaps_individual = availability_service.calculate_availability_overlaps(event.id, show_individual_availability=True)
        print(f"Found {len(overlaps_individual)} result(s):")
        for overlap in overlaps_individual:
            print(f"  - {overlap['start_time']}-{overlap['end_time']} ({overlap['available_guests']})")
        
        # Test 2: Direct service call with show_individual_availability=False (default)
        print(f"\n🔬 Test 2: Direct service call (show_individual=False)")
        overlaps_normal = availability_service.calculate_availability_overlaps(event.id, show_individual_availability=False)
        print(f"Found {len(overlaps_normal)} result(s):")
        for overlap in overlaps_normal:
            print(f"  - {overlap['start_time']}-{overlap['end_time']} ({overlap['available_guests']})")
        
        # Test 3: Handler call (simulates pressing "1" to view current overlaps)
        print(f"\n🔬 Test 3: Handler call (simulates user pressing '1')")
        event_service = EventWorkflowService()
        guest_service = GuestManagementService()
        message_service = MessageFormattingService()
        ai_service = AIProcessingService()
        
        handler = AvailabilityTrackingHandler(event_service, guest_service, message_service, ai_service)
        result = handler.handle_message(event, '1')
        
        print(f"Success: {result.success}")
        print(f"Stage: {result.next_stage}")
        print(f"Message preview:")
        print("=" * 30)
        print(result.message)
        print("=" * 30)
        
        # Expected results
        print(f"\n🎯 Expected Results:")
        print(f"✅ Test 1 should show Aaron's availability (1 result)")
        print(f"✅ Test 2 should show no overlaps (0 results)")  
        print(f"✅ Test 3 should show Aaron's availability in formatted message")
        
        # Cleanup
        print(f"\n🧹 Cleaning up...")
        aaron_availability.delete()
        aaron.delete()
        john.delete()
        event.delete()
        planner.delete()
        
        print(f"✅ Test complete!")

if __name__ == "__main__":
    test_single_guest_overlap_view()
