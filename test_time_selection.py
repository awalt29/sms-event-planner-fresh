#!/usr/bin/env python3
"""Test time selection from partial overlaps"""

from app import create_app, db
from app.models.event import Event
from app.models.planner import Planner
from app.models.guest import Guest
from app.models.availability import Availability
from app.handlers.partial_time_selection_handler import PartialTimeSelectionHandler
from app.services.availability_service import AvailabilityService
from datetime import datetime, date, time as dt_time

app = create_app()

with app.app_context():
    print('=== Testing Time Selection from Partial Overlaps ===\n')
    
    # Clean up any existing test data
    planner = Planner.query.filter_by(phone_number='+1234567890').first()
    if planner:
        db.session.delete(planner)
        db.session.commit()
    
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
    
    # Create some test guests with availability
    guests = []
    guest_names = ['John', 'Mary', 'Mike', 'Sarah']
    for name in guest_names:
        guest = Guest(
            event_id=event.id,
            name=name,
            phone_number=f'+123456789{len(guests)}',
            rsvp_status='accepted' if name != 'Sarah' else 'pending',  # Sarah hasn't responded yet
            availability_provided=name != 'Sarah'
        )
        db.session.add(guest)
        guests.append(guest)
    
    db.session.commit()
    
    # Add availability for first 3 guests (Sarah hasn't responded)
    test_date = date(2024, 8, 16)
    for i, guest in enumerate(guests[:3]):  # Only first 3 guests have responded
        availability = Availability(
            event_id=event.id,
            guest_id=guest.id,
            date=test_date,
            start_time=dt_time(14, 0),  # 2:00 PM
            end_time=dt_time(16, 0),    # 4:00 PM
            preference_level='available'
        )
        db.session.add(availability)
    
    db.session.commit()
    
    print(f'Created event: {event.id} with {len(guests)} guests')
    print(f'3 guests have responded with availability, 1 pending\n')
    
    # Get current overlaps to see what we're working with
    availability_service = AvailabilityService()
    overlaps = availability_service.calculate_availability_overlaps(event.id)
    
    print('Current overlaps:')
    for overlap in overlaps:
        print(f"  {overlap['date']}: {overlap['start_time']}-{overlap['end_time']}")
        print(f"    Available: {', '.join(overlap['available_guests'])}")
    print()
    
    # Set event to partial time selection stage
    event.workflow_stage = 'selecting_partial_time'
    db.session.commit()
    
    # Test selecting the first time slot
    from app.services.event_workflow_service import EventWorkflowService  
    from app.services.guest_management_service import GuestManagementService
    from app.services.message_formatting_service import MessageFormattingService
    from app.services.ai_processing_service import AIProcessingService
    
    # Initialize required services
    event_service = EventWorkflowService()
    guest_service = GuestManagementService()
    message_service = MessageFormattingService()
    ai_service = AIProcessingService()
    
    handler = PartialTimeSelectionHandler(event_service, guest_service, message_service, ai_service)
    body = '1'  # Select first time slot
    
    print(f'Testing time selection with input: "{body}"')
    result = handler.handle_message(event, body)
    
    print(f'Success: {result.success}')
    print(f'New stage: {result.next_stage or "no stage change"}')
    print('Message:')
    print(result.message)
    
    # Check the updated event
    db.session.refresh(event)
    print(f'\nEvent updated:')
    print(f'  Stage: {event.workflow_stage}')
    print(f'  Selected date: {event.selected_date}')
    print(f'  Selected start time: {event.selected_start_time}')
    print(f'  Selected end time: {event.selected_end_time}')
    
    # Clean up
    db.session.delete(planner)
    db.session.commit()
    
print('\n=== Test Complete ===')
