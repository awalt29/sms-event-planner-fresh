import sys
sys.path.append('.')

from app import create_app, db
from app.models.event import Event
from app.models.planner import Planner
from app.models.contact import Contact
from app.handlers.remove_contact_handler import RemoveContactHandler
from app.handlers.contact_removal_handler import ContactRemovalHandler

print('🧪 Testing Multiple Contact Removal - Bulleted List Format')
print('=' * 60)

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
    
    # Create multiple test contacts
    contacts = [
        Contact(planner_id=planner.id, name='Aaron', phone_number='5105935336'),
        Contact(planner_id=planner.id, name='Jude', phone_number='2167046177'),
        Contact(planner_id=planner.id, name='Alex', phone_number='9145606464')
    ]
    db.session.add_all(contacts)
    db.session.commit()
    
    print('Created 3 test contacts: Aaron, Jude, Alex')
    
    # Start remove contact flow
    remove_handler = RemoveContactHandler()
    remove_handler.handle_message(event, 'remove contact')
    
    # Remove multiple contacts (1,2 = Aaron and Jude)
    print('\nRemoving Aaron and Jude (contacts 1,2)')
    removal_handler = ContactRemovalHandler()
    result = removal_handler.handle_message(event, '1,2')
    
    print('\nResponse after removal:')
    print('=' * 50)
    print(result.message)
    print('=' * 50)
    
    # Check formatting
    if 'Removed:' in result.message and '- Aaron' in result.message and '- Jude' in result.message:
        print('✅ SUCCESS: Multiple contacts formatted correctly')
    else:
        print('❌ ISSUE: Multiple contacts not formatted correctly')
    
    # Verify the remaining contact
    lines = result.message.split('\n')
    remaining_contact_lines = [line for line in lines if 'Alex' in line]
    if remaining_contact_lines:
        print('✅ SUCCESS: Alex remains in contact list')
    else:
        print('❌ ISSUE: Alex not found in remaining contacts')
