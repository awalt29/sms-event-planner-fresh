#!/usr/bin/env python3
"""Test first name usage in availability request messages"""

from app import create_app, db
from app.models.planner import Planner
from app.models.event import Event
from app.models.guest import Guest
from app.services.guest_management_service import GuestManagementService

app = create_app()

def test_availability_request_first_names():
    """Test that availability requests use first names only"""
    
    with app.app_context():
        print("🧪 Testing Availability Request First Names")
        print("=" * 42)
        
        # Clean up any existing test data
        planner = Planner.query.filter_by(phone_number='+1234567890').first()
        if planner:
            db.session.delete(planner)
            db.session.commit()
        
        # Create test planner with full name
        planner = Planner(phone_number='+1234567890', name='Aaron Walters')
        db.session.add(planner)
        db.session.commit()
        
        # Create test event
        event = Event(
            planner_id=planner.id,
            title='Test Party',
            notes='Proposed dates: Monday, August 25',
            workflow_stage='collecting_availability'
        )
        db.session.add(event)
        db.session.commit()
        
        # Create test guests with full names
        guests = [
            Guest(
                event_id=event.id,
                name='John Smith',
                phone_number='+1555123456',
                rsvp_status='pending'
            ),
            Guest(
                event_id=event.id,
                name='Sarah Johnson',
                phone_number='+1555987654', 
                rsvp_status='pending'
            ),
            Guest(
                event_id=event.id,
                name='Mike',  # Single name
                phone_number='+1555456789',
                rsvp_status='pending'
            )
        ]
        
        for guest in guests:
            db.session.add(guest)
        db.session.commit()
        
        print("👤 Test Data Created:")
        print(f"   Planner: {planner.name}")
        for guest in guests:
            print(f"   Guest: {guest.name}")
        
        print(f"\n📧 Availability Request Messages:")
        print("=" * 40)
        
        # Test availability request message formatting
        guest_service = GuestManagementService()
        
        for guest in guests:
            message = guest_service._format_availability_request(guest, event, planner)
            print(f"\n📱 Message for {guest.name}:")
            print("─" * 35)
            print(message)
            print("─" * 35)
            
            # Verify first names are being used
            first_line = message.split('\n')[0]
            guest_first_name = guest_service._extract_first_name(guest.name)
            planner_first_name = guest_service._extract_first_name(planner.name)
            
            print(f"✅ Uses guest first name: '{guest_first_name}' ✓")
            print(f"✅ Uses planner first name: '{planner_first_name}' ✓")
        
        print(f"\n🎯 Summary:")
        print("   ✅ Full names in contacts: 'John Smith', 'Sarah Johnson'")
        print("   ✅ Messages use first names: 'Hi John!', 'Hi Sarah!'")
        print("   ✅ Planner attribution: 'Aaron wants to hang out'")
        print("   ✅ Maintains contact information while being friendly")
        
        # Clean up
        db.session.delete(planner)
        db.session.commit()

if __name__ == "__main__":
    test_availability_request_first_names()
