#!/usr/bin/env python3
"""Test continue waiting option from partial time selection"""

from app import create_app, db
from app.models.event import Event
from app.models.planner import Planner
from app.models.guest import Guest
from app.models.availability import Availability
from app.handlers.partial_time_selection_handler import PartialTimeSelectionHandler
from app.services.event_workflow_service import EventWorkflowService  
from app.services.guest_management_service import GuestManagementService
from app.services.message_formatting_service import MessageFormattingService
from app.services.ai_processing_service import AIProcessingService
from datetime import datetime, date, time as dt_time

app = create_app()

with app.app_context():
    print('=== Testing Continue Waiting Option ===\n')
    
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
        workflow_stage='selecting_partial_time'
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
            rsvp_status='accepted' if name != 'Sarah' else 'pending',
            availability_provided=name != 'Sarah'
        )
        db.session.add(guest)
        guests.append(guest)
    
    db.session.commit()
    
    # Add availability for first 3 guests
    test_date = date(2024, 8, 16)
    for i, guest in enumerate(guests[:3]):
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
    
    print(f'Created event: {event.id} with {len(guests)} guests')
    print('3 guests have responded, 1 pending (Sarah)')
    
    # Initialize handler with required services
    event_service = EventWorkflowService()
    guest_service = GuestManagementService()
    message_service = MessageFormattingService()
    ai_service = AIProcessingService()
    
    handler = PartialTimeSelectionHandler(event_service, guest_service, message_service, ai_service)
    
    # Test "continue waiting" option
    body = '2'  # Continue waiting
    
    print(f'\nTesting continue waiting with input: "{body}"')
    result = handler.handle_message(event, body)
    
    print(f'Success: {result.success}')
    print(f'New stage: {result.next_stage or "no stage change"}')
    print('Message:')
    print(result.message)
    
    # Check the updated event
    db.session.refresh(event)
    print(f'\nEvent stage: {event.workflow_stage}')
    
    # Clean up
    db.session.delete(planner)
    db.session.commit()
    
print('\n=== Test Complete ===')
