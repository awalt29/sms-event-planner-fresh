#!/usr/bin/env python3
"""
Test script to verify the "Add guests at confirmation" fix
"""

import requests
import json
import os
import sys

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.event import Event
from app.models.guest import Guest
from app.models.user import User
from app.services.message_formatting_service import MessageFormattingService

def test_add_guests_at_confirmation():
    """Test the add guests at confirmation flow"""
    
    # Use port 5001 for testing
    base_url = "http://localhost:5001"
    
    app = create_app()
    
    with app.app_context():
        # Create test user and event at awaiting_confirmation stage
        user = User.query.filter_by(phone_number='+1234567890').first()
        if not user:
            user = User(phone_number='+1234567890', name='Test Planner')
            db.session.add(user)
            db.session.commit()
        
        # Clean up any existing test events
        Event.query.filter_by(planner_id=user.id).delete()
        db.session.commit()
        
        # Create event at awaiting_confirmation stage
        event = Event(
            planner_id=user.id,
            name="Test Event",
            workflow_stage="awaiting_confirmation",
            selected_dates=json.dumps([{
                'date': '2024-01-20',
                'start_time': '10:00',
                'end_time': '14:00'
            }]),
            overlaps_calculated=False
        )
        db.session.add(event)
        db.session.commit()
        
        # Add one guest initially
        guest = Guest(
            event_id=event.id,
            name="Initial Guest", 
            phone_number="+1111111111"
        )
        db.session.add(guest)
        db.session.commit()
        
        print(f"✅ Created test event {event.id} at awaiting_confirmation stage")
        
        # Test SMS message: selecting option "3" to add more guests
        sms_data = {
            'From': '+1234567890',
            'Body': '3'
        }
        
        print("📱 Sending SMS: '3' (Add more guests)")
        response = requests.post(f"{base_url}/sms", data=sms_data)
        
        print(f"🔍 Response Status: {response.status_code}")
        print(f"🔍 Response Text: {response.text}")
        
        # Check event state after message
        db.session.refresh(event)
        print(f"🔍 Event workflow_stage: {event.workflow_stage}")
        print(f"🔍 Event previous_workflow_stage: {getattr(event, 'previous_workflow_stage', 'Not set')}")
        
        # Test adding a guest
        print("\n📱 Sending SMS: 'John Doe, 555-1234'")
        sms_data['Body'] = 'John Doe, 555-1234'
        response = requests.post(f"{base_url}/sms", data=sms_data)
        
        print(f"🔍 Response Status: {response.status_code}")
        print(f"🔍 Response Text: {response.text}")
        
        # Check if guest was added
        db.session.refresh(event)
        guest_count = Guest.query.filter_by(event_id=event.id).count()
        print(f"🔍 Total guests after addition: {guest_count}")
        
        # Test sending "done"
        print("\n📱 Sending SMS: 'done'")
        sms_data['Body'] = 'done'
        response = requests.post(f"{base_url}/sms", data=sms_data)
        
        print(f"🔍 Response Status: {response.status_code}")
        print(f"🔍 Response Text: {response.text}")
        
        # Final check
        db.session.refresh(event)
        print(f"🔍 Final workflow_stage: {event.workflow_stage}")
        print(f"🔍 Final guest count: {Guest.query.filter_by(event_id=event.id).count()}")

if __name__ == "__main__":
    test_add_guests_at_confirmation()
