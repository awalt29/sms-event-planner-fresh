import sys
sys.path.append('.')

from app import create_app, db
from app.models.event import Event
from app.models.planner import Planner
from app.models.contact import Contact
from app.handlers.remove_contact_handler import RemoveContactHandler
from app.handlers.contact_removal_handler import ContactRemovalHandler

print('🧪 Testing Contact Removal - Return to Main Menu')
print('=' * 50)

app = create_app()

with app.app_context():
    # Clean up and recreate test data
    planner = Planner.query.filter_by(phone_number='1234567890').first()
    if planner:
        db.session.delete(planner)
        db.session.commit()
    
    planner = Planner(phone_number='1234567890', name='Test Planner')
    db.session.add(planner)
    db.session.commit()
    
    event = Event(planner_id=planner.id, title='Test', workflow_stage='collecting_guests')
    db.session.add(event)
    db.session.commit()
    
    # Create test contacts
    contacts = [
        Contact(planner_id=planner.id, name='John', phone_number='5105935336'),
        Contact(planner_id=planner.id, name='Jude', phone_number='2167046177'),
    ]
    db.session.add_all(contacts)
    db.session.commit()
    
    print('Created 2 test contacts: John, Jude')
    print(f'Original event stage: {event.workflow_stage}')
    
    # Start remove contact flow
    remove_handler = RemoveContactHandler()
    remove_handler.handle_message(event, 'remove contact')
    
    # Remove one contact 
    print('\nRemoving Jude (contact 2)')
    removal_handler = ContactRemovalHandler()
    result = removal_handler.handle_message(event, '2')
    
    print('\nResponse after removal:')
    print('=' * 40)
    print(result.message)
    print('=' * 40)
    
    # Check if it returns to guest collection stage
    if "Who's coming?" in result.message:
        print('✅ SUCCESS: Returns to guest collection stage')
    else:
        print('❌ ISSUE: Does not return to guest collection stage')
    
    # Check that stage is back to collecting_guests
    print(f'\nNew event stage: {result.next_stage}')
    if result.next_stage == 'collecting_guests':
        print('✅ SUCCESS: Stage returned to collecting_guests')
    else:
        print(f'❌ ISSUE: Stage is {result.next_stage}, should be collecting_guests')
    
    # Check for guest collection elements
    guest_elements = ['Previous contacts:', 'Select contacts', 'Add one guest at a time', 'Commands:']
    missing_elements = []
    for element in guest_elements:
        if element not in result.message:
            missing_elements.append(element)
    
    if not missing_elements:
        print('✅ SUCCESS: All guest collection elements present')
    else:
        print(f'❌ ISSUE: Missing elements: {missing_elements}')
