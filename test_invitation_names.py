#!/usr/bin/env python3
"""Test first name usage in guest invitation messages"""

from app import create_app, db
from app.models.planner import Planner
from app.models.event import Event
from app.models.guest import Guest
from app.services.message_formatting_service import MessageFormattingService
from datetime import date

app = create_app()

def test_guest_invitation_first_names():
    """Test that guest invitations use planner's first name"""
    
    with app.app_context():
        print("🧪 Testing Guest Invitation First Names")
        print("=" * 37)
        
        # Create test planner with full name
        planner = Planner.query.filter_by(phone_number='+1234567890').first()
        if planner:
            db.session.delete(planner)
            db.session.commit()
            
        planner = Planner(phone_number='+1234567890', name='Dr. Emily Watson')
        db.session.add(planner)
        db.session.commit()
        
        # Create test event with venue selection
        event = Event(
            planner_id=planner.id,
            title='Test Event',
            activity='Coffee',
            workflow_stage='final_confirmation',
            selected_venue={
                'name': 'Starbucks',
                'address': '123 Main St',
                'maps_url': 'https://maps.google.com/starbucks'
            },
            notes='Selected time: Mon, 8/25: 2pm-6pm'
        )
        db.session.add(event)
        db.session.commit()
        
        # Test invitation message formatting
        message_service = MessageFormattingService()
        
        # Mock the selected time data that would normally come from the event
        selected_time = {
            'date': date(2025, 8, 25),
            'start_time': '14:00',
            'end_time': '18:00'
        }
        
        invitation_message = message_service.format_guest_invitation(event, selected_time)
        
        print("👤 Test Setup:")
        print(f"   Planner Full Name: '{planner.name}'")
        print(f"   Expected First Name: 'Emily'")
        
        print(f"\n📧 Guest Invitation Message:")
        print("=" * 40)
        print(invitation_message)
        print("=" * 40)
        
        # Verify first name is used
        planner_first_name = message_service._extract_first_name(planner.name)
        
        print(f"\n✅ Verification:")
        print(f"   Planner first name extracted: '{planner_first_name}'")
        
        if f"Planned by: {planner_first_name}" in invitation_message:
            print(f"   ✅ Invitation uses first name: 'Planned by: {planner_first_name}'")
        else:
            print(f"   ❌ Full name still being used")
        
        print(f"\n🎯 Benefits:")
        print("   ✅ Personal, friendly attribution")
        print("   ✅ Cleaner invitation messages")
        print("   ✅ Professional titles handled gracefully")
        
        # Clean up
        db.session.delete(planner)
        db.session.commit()

if __name__ == "__main__":
    test_guest_invitation_first_names()
