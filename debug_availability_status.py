#!/usr/bin/env python3
"""Debug the availability status workflow"""

from app import create_app, db
from app.models.event import Event
from app.models.planner import Planner
from app.models.guest import Guest
from app.models.availability import Availability
from app.services.message_formatting_service import MessageFormattingService
from datetime import date, time as dt_time

app = create_app()

with app.app_context():
    print('=== Debugging Availability Status Workflow ===\n')
    
    # Check if there are any existing events that might have old state
    planners = Planner.query.all()
    print(f'Found {len(planners)} planners in database:')
    
    for planner in planners:
        print(f'  - {planner.phone_number}: {planner.name}')
        events = Event.query.filter_by(planner_id=planner.id).all()
        for event in events:
            print(f'    Event {event.id}: {event.title} - Stage: {event.workflow_stage}')
            guests = Guest.query.filter_by(event_id=event.id).all()
            print(f'      Guests: {len(guests)} total')
            for guest in guests:
                print(f'        - {guest.name}: rsvp={guest.rsvp_status}, avail={guest.availability_provided}')
    
    print('\\n=== Testing Message Formatting Service ===')
    
    # Find an event in collecting_availability stage
    events_in_availability = Event.query.filter_by(workflow_stage='collecting_availability').all()
    if events_in_availability:
        event = events_in_availability[0]
        print(f'\\nTesting with event {event.id} in stage: {event.workflow_stage}')
        
        message_service = MessageFormattingService()
        status_msg = message_service.format_availability_status(event)
        
        print('Status message output:')
        print('=' * 50)
        print(status_msg)
        print('=' * 50)
        
        # Check if "Press 1" is in the message
        if "Press 1 to view current overlaps" in status_msg:
            print('\\n✅ "Press 1" instruction is present!')
        else:
            print('\\n❌ "Press 1" instruction is missing!')
    else:
        print('\\nNo events found in collecting_availability stage')

print('\\n=== Debug Complete ===')
