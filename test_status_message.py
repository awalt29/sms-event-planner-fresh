#!/usr/bin/env python3
"""Test availability status message with 1/2 guests responded"""

from app import create_app, db
from app.models.event import Event
from app.models.planner import Planner
from app.models.guest import Guest
from app.models.availability import Availability
from app.services.message_formatting_service import MessageFormattingService
from datetime import datetime, date, time as dt_time

app = create_app()

with app.app_context():
    print('=== Testing Availability Status Message (1/2 responded) ===\n')
    
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
    
    # Create 2 guests: 1 responded, 1 pending (like in the screenshot)
    guest1 = Guest(
        event_id=event.id,
        name='John Kim',
        phone_number='+1234567890',
        rsvp_status='accepted',
        availability_provided=True  # Has responded
    )
    db.session.add(guest1)
    
    guest2 = Guest(
        event_id=event.id,
        name='Sarah',
        phone_number='+1234567891',
        rsvp_status='pending',
        availability_provided=False  # Hasn't responded
    )
    db.session.add(guest2)
    
    db.session.commit()
    
    # Add availability for the first guest
    availability = Availability(
        event_id=event.id,
        guest_id=guest1.id,
        date=date(2024, 8, 16),
        start_time=dt_time(14, 0),
        end_time=dt_time(16, 0),
        preference_level='available'
    )
    db.session.add(availability)
    db.session.commit()
    
    print(f'Created scenario:')
    print(f'  - Event: {event.title}')
    print(f'  - Guest 1: {guest1.name} (responded)')
    print(f'  - Guest 2: {guest2.name} (pending)')
    print()
    
    # Test the message formatting
    message_service = MessageFormattingService()
    status_message = message_service.format_availability_status(event)
    
    print('Status message:')
    print(status_message)
    
    # Check if "Press 1" option is included
    if "Press 1 to view current overlaps" in status_message:
        print('\n✅ "Press 1" option is correctly included!')
    else:
        print('\n❌ "Press 1" option is missing!')
    
    # Clean up
    db.session.delete(planner)
    db.session.commit()
    
print('\n=== Test Complete ===')
