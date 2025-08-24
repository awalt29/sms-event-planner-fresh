import sys
sys.path.append('.')

from app import create_app, db
from app.models.event import Event
from app.models.planner import Planner
from app.models.guest import Guest
from app.models.guest_state import GuestState
from app.handlers.guest_availability_handler import GuestAvailabilityHandler
from app.services.ai_processing_service import AIProcessingService
from app.services.event_workflow_service import EventWorkflowService
from app.services.guest_management_service import GuestManagementService
from app.services.message_formatting_service import MessageFormattingService

print('🧪 Testing Multi-Day Still Requires Day Names')
print('=' * 50)

app = create_app()

with app.app_context():
    # Clean up any existing test data
    planner = Planner.query.filter_by(phone_number='1234567891').first()
    if planner:
        db.session.delete(planner)
        db.session.commit()
    
    # Create test data
    planner = Planner(phone_number='1234567891', name='Test Planner 2')
    db.session.add(planner)
    db.session.commit()
    
    event = Event(planner_id=planner.id, title='Multi Day Party', workflow_stage='collecting_availability')
    db.session.add(event)
    db.session.commit()
    
    guest = Guest(event_id=event.id, name='Test Guest 2', phone_number='9876543211')
    db.session.add(guest)
    db.session.commit()
    
    # Create guest state with MULTI DAY event context
    state_data = {
        'event_dates': ['2025-08-15', '2025-08-16', '2025-08-18']  # Friday, Saturday, Monday
    }
    guest_state = GuestState(
        phone_number='9876543211',
        current_state='awaiting_availability',
        event_id=event.id
    )
    guest_state.set_state_data(state_data)
    db.session.add(guest_state)
    db.session.commit()
    
    # Create handler
    ai_service = AIProcessingService()
    event_service = EventWorkflowService()
    guest_service = GuestManagementService()
    message_service = MessageFormattingService()
    
    handler = GuestAvailabilityHandler(event_service, guest_service, message_service, ai_service)
    
    # Test that multi-day events still require day names
    test_inputs = [
        ("2-4", "should be rejected"),           # No day - should fail
        ("afternoon", "should be accepted"),     # Generic period - should work 
        ("Friday 2-4", "should be accepted"),   # With day - should work
    ]
    
    print("Testing multi-day availability (should require day names):")
    print("-" * 55)
    
    for input_text, expectation in test_inputs:
        print(f"\n📝 Testing input: '{input_text}' ({expectation})")
        
        try:
            response = handler.handle_availability_response(guest_state, input_text)
            
            if "Got it!" in response:
                print("✅ ACCEPTED: Availability parsed successfully")
                print(f"Response preview: {response[:100]}...")
            else:
                print("❌ REJECTED: Availability not understood")
                print(f"Error response: {response[:100]}...")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            
        # Reset guest state for next test
        guest_state.current_state = 'awaiting_availability'
        guest_state.save()
    
    print("\n" + "=" * 50)
    print("Summary: Multi-day events should still work as before!")
