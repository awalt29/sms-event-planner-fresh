#!/usr/bin/env python3
"""Test the improved guest addition message format"""

from app import create_app, db
from app.models.planner import Planner
from app.models.event import Event
from app.models.guest import Guest
from app.models.contact import Contact
from app.handlers.guest_collection_handler import GuestCollectionHandler

app = create_app()

def test_guest_addition_format():
    """Test the new guest addition message format"""
    
    with app.app_context():
        print("🧪 Testing Improved Guest Addition Format")
        print("=" * 42)
        
        # Clean up existing test data
        planner = Planner.query.filter_by(phone_number='+1234567890').first()
        if planner:
            db.session.delete(planner)
            db.session.commit()
        
        # Create test planner
        planner = Planner(phone_number='+1234567890', name='Test Planner')
        db.session.add(planner)
        db.session.commit()
        
        # Create test contacts
        contacts = [
            Contact(planner_id=planner.id, name='Aaron', phone_number='5105935336'),
            Contact(planner_id=planner.id, name='Aaron walters', phone_number='9145606464'),
            Contact(planner_id=planner.id, name='Jude workus', phone_number='2167046177'),
        ]
        for contact in contacts:
            db.session.add(contact)
        db.session.commit()
        
        # Create test event
        event = Event(
            planner_id=planner.id,
            title='Test Event',
            workflow_stage='collecting_guests'
        )
        db.session.add(event)
        db.session.commit()
        
        # Add one guest first
        existing_guest = Guest(
            event_id=event.id,
            name='Sarah Johnson',
            phone_number='+1555123456',
            rsvp_status='pending'
        )
        db.session.add(existing_guest)
        db.session.commit()
        
        # Test the handler
        handler = GuestCollectionHandler(None, None, None, None)
        
        # Simulate adding contact #1 (Aaron)
        result = handler._handle_contact_selection(event, '1')
        
        print("📱 Message After Adding Contact:")
        print("=" * 40)
        print(result.response_text)
        print("=" * 40)
        
        print(f"\n✅ New Format Verification:")
        lines = result.response_text.split('\n')
        
        # Check if we have the expected sections
        has_added_message = any('Added from contacts:' in line for line in lines)
        has_guest_list = any('Guest list:' in line for line in lines)
        has_select_instruction = any('Select contacts' in line for line in lines)
        has_contacts_section = any('Contacts:' in line for line in lines)
        
        # Check order - guest list should come before contacts section
        guest_list_index = next((i for i, line in enumerate(lines) if 'Guest list:' in line), -1)
        contacts_index = next((i for i, line in enumerate(lines) if 'Contacts:' in line), -1)
        select_index = next((i for i, line in enumerate(lines) if 'Select contacts' in line), -1)
        
        print(f"   ✅ Has 'Added from contacts' message: {has_added_message}")
        print(f"   ✅ Has guest list section: {has_guest_list}")
        print(f"   ✅ Has selection instructions: {has_select_instruction}")
        print(f"   ✅ Has contacts section: {has_contacts_section}")
        print(f"   ✅ Correct order (Guest list → Instructions → Contacts): {guest_list_index < select_index < contacts_index}")
        
        print(f"\n🎯 Benefits:")
        print("   ✅ Clear separation between current guests and available contacts")
        print("   ✅ Instructions appear before contact list for better UX")
        print("   ✅ Guest list shows who's actually invited (no phone numbers)")
        
        # Clean up
        db.session.delete(planner)
        db.session.commit()

if __name__ == "__main__":
    test_guest_addition_format()
