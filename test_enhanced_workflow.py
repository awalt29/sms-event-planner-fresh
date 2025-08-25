#!/usr/bin/env python3
"""Comprehensive test of enhanced availability collection workflow"""

from app import create_app, db
from app.models.event import Event
from app.models.planner import Planner
from app.models.guest import Guest
from app.models.availability import Availability
from app.handlers.availability_tracking_handler import AvailabilityTrackingHandler
from app.handlers.partial_time_selection_handler import PartialTimeSelectionHandler
from app.services.event_workflow_service import EventWorkflowService  
from app.services.guest_management_service import GuestManagementService
from app.services.message_formatting_service import MessageFormattingService
from app.services.ai_processing_service import AIProcessingService
from datetime import datetime, date, time as dt_time

app = create_app()

def cleanup_test_data():
    """Clean up any existing test data"""
    planner = Planner.query.filter_by(phone_number='+1234567890').first()
    if planner:
        db.session.delete(planner)
        db.session.commit()

def create_test_scenario():
    """Create test scenario with partial responses"""
    # Create test planner
    planner = Planner(phone_number='+1234567890', name='Test Planner')
    db.session.add(planner)
    db.session.commit()
    
    # Create test event
    event = Event(
        planner_id=planner.id,
        title='Test Party',
        activity='Dinner',
        workflow_stage='collecting_availability'
    )
    db.session.add(event)
    db.session.commit()
    
    # Create guests
    guests = []
    guest_names = ['John', 'Mary', 'Mike', 'Sarah', 'Alex']
    for name in guest_names:
        guest = Guest(
            event_id=event.id,
            name=name,
            phone_number=f'+123456789{len(guests)}',
            rsvp_status='accepted' if name in ['John', 'Mary', 'Mike'] else 'pending',
            availability_provided=name in ['John', 'Mary', 'Mike']  # Only 3/5 responded
        )
        db.session.add(guest)
        guests.append(guest)
    
    db.session.commit()
    
    # Add availability for responded guests
    test_date = date(2024, 8, 16)
    for guest in guests[:3]:  # Only John, Mary, Mike have responded
        availability = Availability(
            event_id=event.id,
            guest_id=guest.id,
            date=test_date,
            start_time=dt_time(14, 0),
            end_time=dt_time(16, 0),
            preference_level='available'
        )
        db.session.add(availability)
    
    db.session.commit()
    
    return event, guests

with app.app_context():
    print('=== Enhanced Availability Collection Workflow Test ===\n')
    
    cleanup_test_data()
    event, guests = create_test_scenario()
    
    print(f'Created scenario:')
    print(f'  - Event: {event.title}')
    print(f'  - Total guests: {len(guests)}')
    print(f'  - Responded: 3 (John, Mary, Mike)')
    print(f'  - Pending: 2 (Sarah, Alex)')
    print(f'  - Stage: {event.workflow_stage}\\n')
    
    # Initialize services
    event_service = EventWorkflowService()
    guest_service = GuestManagementService()
    message_service = MessageFormattingService()
    ai_service = AIProcessingService()
    
    # Test 1: Availability tracking with partial overlap request
    print('🧪 Test 1: Request partial overlaps from availability tracking')
    availability_handler = AvailabilityTrackingHandler(event_service, guest_service, message_service, ai_service)
    
    result = availability_handler.handle_message(event, '1')  # Press 1 to view overlaps
    print(f'Success: {result.success}')
    print(f'Next stage: {result.next_stage}')
    print('Message:')
    print(result.message)
    print()
    
    # Update event stage for next test
    event.workflow_stage = 'selecting_partial_time'
    db.session.commit()
    
    # Test 2: Select a time slot from partial responses
    print('🧪 Test 2: Select time slot from partial responses')
    partial_handler = PartialTimeSelectionHandler(event_service, guest_service, message_service, ai_service)
    
    result = partial_handler.handle_message(event, '1')  # Select first time slot
    print(f'Success: {result.success}')
    print(f'Next stage: {result.next_stage}')
    print('Selected time details:')
    db.session.refresh(event)
    print(f'  Date: {event.selected_date}')
    print(f'  Time: {event.selected_start_time} - {event.selected_end_time}')
    print('Message:')
    print(result.message)
    print()
    
    # Test 3: Continue waiting option
    print('🧪 Test 3: Test continue waiting option')
    
    # Reset for continue waiting test
    event.workflow_stage = 'selecting_partial_time'
    event.selected_date = None
    event.selected_start_time = None
    event.selected_end_time = None
    db.session.commit()
    
    result = partial_handler.handle_message(event, '2')  # Continue waiting
    print(f'Success: {result.success}')
    print(f'Next stage: {result.next_stage}')
    print('Message:')
    print(result.message)
    print()
    
    # Test 4: Add a late arrival (simulate someone responding after partial selection)
    print('🧪 Test 4: Simulate late arrival')
    
    # Set event back to availability tracking
    event.workflow_stage = 'tracking_availability'
    db.session.commit()
    
    # Mark Sarah as having provided availability (late arrival)
    sarah = next(g for g in guests if g.name == 'Sarah')
    sarah.availability_provided = True
    sarah.rsvp_status = 'accepted'
    
    # Add Sarah's availability
    availability = Availability(
        event_id=event.id,
        guest_id=sarah.id,
        date=date(2024, 8, 16),
        start_time=dt_time(13, 0),  # Different time
        end_time=dt_time(15, 0),
        preference_level='available'
    )
    db.session.add(availability)
    db.session.commit()
    
    print('Sarah has now responded with availability 13:00-15:00')
    
    # Test partial overlap request with updated availability
    result = availability_handler.handle_message(event, '1')
    print(f'Updated overlap view - Success: {result.success}')
    print('Message:')
    print(result.message)
    
    # Cleanup
    cleanup_test_data()
    
print('\\n=== All Tests Complete ===')
