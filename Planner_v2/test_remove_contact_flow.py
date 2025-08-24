#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

from app import create_app, db
from app.models.event import Event
from app.models.planner import Planner
from app.models.contact import Contact
from app.handlers.remove_contact_handler import RemoveContactHandler
from app.handlers.contact_removal_handler import ContactRemovalHandler

def test_remove_contact_flow():
    """Test the updated remove contact flow"""
    
    app = create_app()
    
    with app.app_context():
        print("🧪 Testing Updated Remove Contact Flow")
        print("=" * 50)
        
        # Clean up any existing test data
        planner = Planner.query.filter_by(phone_number='1234567890').first()
        if planner:
            db.session.delete(planner)
            db.session.commit()
        
        # Create test planner
        planner = Planner(phone_number='1234567890', name='Test Planner')
        db.session.add(planner)
        db.session.commit()
        
        # Create test event
        event = Event(
            planner_id=planner.id,
            title='Test Party',
            workflow_stage='collecting_guests'
        )
        db.session.add(event)
        db.session.commit()
        
        # Create test contacts
        contact1 = Contact(planner_id=planner.id, name='John', phone_number='5105935336')
        contact2 = Contact(planner_id=planner.id, name='Jude', phone_number='2167046177')
        contact3 = Contact(planner_id=planner.id, name='Alex', phone_number='9145606464')
        db.session.add_all([contact1, contact2, contact3])
        db.session.commit()
        
        print(f"Created 3 test contacts: {contact1.name}, {contact2.name}, {contact3.name}")
        
        # Test 1: Initiate remove contact
        print("\n📝 Test 1: Initiate remove contact")
        remove_handler = RemoveContactHandler()
        result = remove_handler.handle_message(event, 'remove contact')
        
        print("Response:")
        print(result.message)
        print(f"New workflow stage: {result.new_workflow_stage}")
        
        # Check that cancel option is removed
        if "Cancel" not in result.message and "restart" in result.message:
            print("✅ Cancel option removed, restart instruction added")
        else:
            print("❌ Cancel option still present or restart instruction missing")
        
        # Test 2: Remove single contact
        print("\n📝 Test 2: Remove single contact (Jude)")
        removal_handler = ContactRemovalHandler()
        result = removal_handler.handle_message(event, '2')  # Jude
        
        print("Response:")
        print(result.message)
        print(f"New workflow stage: {result.new_workflow_stage}")
        
        # Check that Jude was removed
        remaining_contacts = Contact.query.filter_by(planner_id=planner.id).all()
        print(f"Contacts remaining: {[c.name for c in remaining_contacts]}")
        
        if "Removed **Jude**" in result.message:
            print("✅ Correct format used for single removal")
        else:
            print("❌ Incorrect format for single removal")
        
        # Test 3: Try multiple contact removal
        print("\n📝 Test 3: Initiate remove contact again")
        event.workflow_stage = 'collecting_guests'
        event.save()
        
        result = remove_handler.handle_message(event, 'remove contact')
        print("Contacts to remove:")
        print(result.message)
        
        print("\n📝 Test 4: Remove multiple contacts (1,2)")
        result = removal_handler.handle_message(event, '1,2')  # John and Alex
        
        print("Response:")
        print(result.message)
        
        # Check final contacts
        final_contacts = Contact.query.filter_by(planner_id=planner.id).all()
        print(f"Final contacts remaining: {[c.name for c in final_contacts]}")
        
        if "Removed **" in result.message and len(final_contacts) == 0:
            print("✅ Multiple contact removal works")
        else:
            print("❌ Multiple contact removal failed")
        
        # Test 5: Restart functionality
        print("\n📝 Test 5: Test restart functionality")
        
        # Add a contact back for testing
        test_contact = Contact(planner_id=planner.id, name='Test', phone_number='1111111111')
        db.session.add(test_contact)
        db.session.commit()
        
        # Start removal flow
        event.workflow_stage = 'collecting_guests'
        event.save()
        remove_handler.handle_message(event, 'remove contact')
        
        # Test restart
        result = removal_handler.handle_message(event, 'restart')
        print("Restart response:")
        print(result.message)
        print(f"Workflow stage after restart: {result.new_workflow_stage}")
        
        if result.new_workflow_stage == 'collecting_guests':
            print("✅ Restart returns to correct stage")
        else:
            print("❌ Restart doesn't return to correct stage")

if __name__ == "__main__":
    test_remove_contact_flow()
