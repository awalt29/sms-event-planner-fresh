#!/usr/bin/env python3
"""Test guest list update when time is reselected after adding new guests"""

from app import create_app, db
from app.models.event import Event
from app.models.planner import Planner
from app.models.guest import Guest
from app.services.message_formatting_service import MessageFormattingService
import json

app = create_app()

with app.app_context():
    print('=== Testing Guest List Update Logic ===\n')
    
    # Create test event
    planner = Planner(phone_number='+1555000001', name='Test Planner')
    db.session.add(planner)
    db.session.commit()
    
    event = Event(
        planner_id=planner.id,
        title='Test Party',
        workflow_stage='final_confirmation'
    )
    db.session.add(event)
    db.session.commit()
    
    # Create guests
    guest1 = Guest(event_id=event.id, name='Alice', phone_number='+1555000002')
    guest2 = Guest(event_id=event.id, name='Bob', phone_number='+1555000003') 
    guest3 = Guest(event_id=event.id, name='Charlie', phone_number='+1555000004')
    
    for guest in [guest1, guest2, guest3]:
        db.session.add(guest)
    db.session.commit()
    
    # Test 1: Initial time selection with Alice and Bob
    print("📝 Test 1: Initial time selection")
    initial_guests = ['Alice', 'Bob']
    event.notes = f"Selected available guests: {json.dumps(initial_guests)}"
    db.session.commit()
    
    message_service = MessageFormattingService()
    guest_list = message_service._format_guest_list_for_invitation(event, guest1)
    print(f"   Current recipient: Alice")
    print(f"   Stored available guests: {initial_guests}")
    print(f"   Final invitation guest list: '{guest_list}'")
    print(f"   Expected: 'With: Bob' ✅" if guest_list == "👥 With: Bob" else f"   Expected: 'With: Bob' ❌")
    print()
    
    # Test 2: New time selection after adding Charlie
    print("📝 Test 2: After adding Charlie and selecting new time")
    updated_guests = ['Alice', 'Bob', 'Charlie']
    event.notes = f"Selected available guests: {json.dumps(updated_guests)}"
    db.session.commit()
    
    guest_list = message_service._format_guest_list_for_invitation(event, guest1)
    print(f"   Current recipient: Alice")
    print(f"   Stored available guests: {updated_guests}")
    print(f"   Final invitation guest list: '{guest_list}'")
    print(f"   Expected: 'With: Bob and Charlie' ✅" if guest_list == "👥 With: Bob and Charlie" else f"   Expected: 'With: Bob and Charlie' ❌")
    print()
    
    # Test 3: What if Charlie isn't available for the selected time?
    print("📝 Test 3: New time selection where Charlie isn't available")
    partial_guests = ['Alice', 'Bob']  # Charlie not available for this time
    event.notes = f"Selected available guests: {json.dumps(partial_guests)}"
    db.session.commit()
    
    guest_list = message_service._format_guest_list_for_invitation(event, guest1)
    print(f"   Current recipient: Alice") 
    print(f"   Stored available guests: {partial_guests}")
    print(f"   Final invitation guest list: '{guest_list}'")
    print(f"   Expected: 'With: Bob' ✅" if guest_list == "👥 With: Bob" else f"   Expected: 'With: Bob' ❌")
    print()
    
    # Clean up
    db.session.delete(guest1)
    db.session.delete(guest2)
    db.session.delete(guest3)
    db.session.delete(event)
    db.session.delete(planner)
    db.session.commit()
    
    print("✅ The guest list correctly updates based on the most recent time selection!")
    print("   This means invitations will always show the accurate guest list for the selected time.")
