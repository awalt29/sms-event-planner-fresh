#!/usr/bin/env python3
"""
Test RSVP guest state cleanup
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models.planner import Planner
from app.models.event import Event
from app.models.guest import Guest
from app.models.guest_state import GuestState
from app.routes.sms import SMSRouter

def test_rsvp_cleanup():
    """Test that guest states are cleaned up after RSVP responses"""
    app = create_app()
    
    with app.app_context():
        # Create test data
        planner = Planner(name="Test Planner", phone_number="+1234567890")
        planner.save()
        
        event = Event(
            planner_id=planner.id,
            title="Test Event",
            workflow_stage="final_confirmation",
            status="planning"
        )
        event.save()
        
        guest = Guest(
            name="Test Guest",
            phone_number="2125551234",  # Use normalized format (NYC number)
            event_id=event.id
        )
        guest.save()
        
        # Create guest state for RSVP
        guest_state = GuestState(
            phone_number="2125551234",  # Use normalized format
            event_id=event.id,
            current_state="awaiting_rsvp"
        )
        guest_state.save()
        
        print(f"Created guest state ID: {guest_state.id}")
        
        # Debug: Check if guest state exists after creation
        found_state = GuestState.query.filter_by(phone_number="2125551234").first()
        print(f"Guest state found after creation: {found_state is not None}")
        if found_state:
            print(f"  State: {found_state.current_state}")
            print(f"  Phone: {found_state.phone_number}")
        
        # Initialize SMS router
        router = SMSRouter()
        
        # Debug: Test phone normalization
        normalized = router._normalize_phone("+12125551234")
        print(f"Normalized phone: {normalized}")
        
        # Test RSVP response
        response = router.route_message("+12125551234", "Yes")
        print(f"RSVP response: {response}")
        
        # Check if guest state was cleaned up
        remaining_states = GuestState.query.filter_by(phone_number="2125551234").all()
        print(f"Remaining guest states: {len(remaining_states)}")
        
        if len(remaining_states) == 0:
            print("✅ SUCCESS: Guest state was properly cleaned up after RSVP")
        else:
            print("❌ FAILED: Guest state was not cleaned up")
            for state in remaining_states:
                print(f"  - State: {state.current_state}")
        
        # Check guest RSVP status
        updated_guest = Guest.query.get(guest.id)
        print(f"Guest RSVP status: {updated_guest.rsvp_status}")
        
        # Clean up test data
        for state in remaining_states:
            state.delete()
        guest.delete()
        event.delete()
        planner.delete()

if __name__ == "__main__":
    test_rsvp_cleanup()
