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

print('🧪 Testing Single-Day Time-Only Availability')
print('=' * 50)

app = create_app()

with app.app_context():
    # Clean up any existing test data
    planner = Planner.query.filter_by(phone_number='1234567890').first()
    if planner:
        db.session.delete(planner)
        db.session.commit()
    
    # Create test data
    planner = Planner(phone_number='1234567890', name='Test Planner')
    db.session.add(planner)
    db.session.commit()
    
    event = Event(planner_id=planner.id, title='Single Day Party', workflow_stage='collecting_availability')
    db.session.add(event)
    db.session.commit()
    
    guest = Guest(event_id=event.id, name='Test Guest', phone_number='9876543210')
    db.session.add(guest)
    db.session.commit()
    
    # Create guest state with SINGLE DAY event context
    state_data = {
        'event_dates': ['2025-08-15']  # Only Friday
    }
    guest_state = GuestState(
        phone_number='9876543210',
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
    
    # Test time-only inputs for single day event
    test_inputs = [
        "2-4",           # Should work now - time only
        "2-4pm",         # Should work now - time only with PM
        "from 2-4",      # Should work now - time only with "from"
        "afternoon",     # Should work now - period only
        "morning",       # Should work now - period only
        "after 2pm",     # Should work now - after time only
        "all day",       # Should work now - all day only
        "Friday 2-4"     # Should still work - with day name
    ]
    
    print("Testing single-day time-only availability:")
    print("-" * 50)
    
    for input_text in test_inputs:
        print(f"\n📝 Testing input: '{input_text}'")
        
        try:
            response = handler.handle_availability_response(guest_state, input_text)
            
            if "Got it!" in response:
                print("✅ SUCCESS: Time-only availability parsed and accepted")
                # Extract the date part to show it used the single day
                if "Fri 8/15:" in response:
                    print("✅ CONFIRMED: Used single event date (Friday 8/15)")
                print(f"Response preview: {response[:100]}...")
            else:
                print("❌ FAILED: Time-only availability not understood")
                print(f"Error response: {response}")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            
        # Reset guest state for next test
        guest_state.current_state = 'awaiting_availability'
        guest_state.save()
    
    print("\n" + "=" * 50)
    print("Summary: Single-day events should now accept time-only inputs!")
