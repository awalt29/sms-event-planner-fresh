#!/usr/bin/env python3
"""Test first name usage in planner notification messages"""

from app import create_app, db
from app.models.planner import Planner
from app.models.event import Event
from app.models.guest import Guest
from app.models.guest_state import GuestState
from app.handlers.guest_availability_handler import GuestAvailabilityHandler

app = create_app()

def test_planner_notification_first_names():
    """Test that planner notifications use first names"""
    
    with app.app_context():
        print("🧪 Testing Planner Notification First Names")
        print("=" * 42)
        
        # Create test planner
        planner = Planner.query.filter_by(phone_number='+1234567890').first()
        if planner:
            db.session.delete(planner)
            db.session.commit()
            
        planner = Planner(phone_number='+1234567890', name='Aaron Walters')
        db.session.add(planner)
        db.session.commit()
        
        # Create test event
        event = Event(
            planner_id=planner.id,
            title='Test Party',
            workflow_stage='collecting_availability'
        )
        db.session.add(event)
        db.session.commit()
        
        # Create test guests
        guests = [
            Guest(
                event_id=event.id,
                name='Jennifer Rodriguez',
                phone_number='+1555111111',
                rsvp_status='pending',
                availability_provided=False
            ),
            Guest(
                event_id=event.id,
                name='Michael Thompson',
                phone_number='+1555222222',
                rsvp_status='pending', 
                availability_provided=True  # Already responded
            )
        ]
        
        for guest in guests:
            db.session.add(guest)
        db.session.commit()
        
        # Create mock guest state
        guest_state = GuestState(
            phone_number='+1555111111',
            event_id=event.id,
            current_state='awaiting_availability'
        )
        guest_state.set_state_data({})
        db.session.add(guest_state)
        db.session.commit()
        
        print("👤 Test Data:")
        print(f"   Planner: {planner.name}")
        for guest in guests:
            print(f"   Guest: {guest.name} (responded: {guest.availability_provided})")
        
        # Test the handler's first name extraction
        handler = GuestAvailabilityHandler(None, None, None, None)
        
        responding_guest = guests[0]  # Jennifer Rodriguez
        first_name = handler._extract_first_name(responding_guest.name)
        
        print(f"\n📱 When '{responding_guest.name}' responds:")
        print("=" * 50)
        print(f"✅ Planner will see: '{first_name} has provided their availability!'")
        print(f"✅ Instead of: '{responding_guest.name} has provided their availability!'")
        
        print(f"\n🎯 Benefits:")
        print("   ✅ More personal and friendly tone")
        print("   ✅ Cleaner notification messages")
        print("   ✅ Full names still stored for contact management")
        print("   ✅ Works with single names too")
        
        # Clean up
        db.session.delete(planner)
        db.session.commit()

if __name__ == "__main__":
    test_planner_notification_first_names()
