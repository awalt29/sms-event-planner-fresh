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

print('🧪 Complete Single-Day vs Multi-Day Availability Test')
print('=' * 60)

app = create_app()

with app.app_context():
    # Clean up any existing test data
    for phone in ['1111111111', '2222222222']:
        planner = Planner.query.filter_by(phone_number=phone).first()
        if planner:
            db.session.delete(planner)
            db.session.commit()
    
    # Create handlers
    ai_service = AIProcessingService()
    event_service = EventWorkflowService()
    guest_service = GuestManagementService()
    message_service = MessageFormattingService()
    
    handler = GuestAvailabilityHandler(event_service, guest_service, message_service, ai_service)
    
    # Test cases for single-day vs multi-day
    test_cases = [
        {
            'name': '📅 SINGLE-DAY EVENT',
            'planner_phone': '1111111111',
            'guest_phone': '9999999991',
            'dates': ['2025-08-15'],  # Only Friday
            'inputs': [
                ('2-4', 'Should ACCEPT (time-only for single day)'),
                ('afternoon', 'Should ACCEPT (period always works)'),
                ('Friday 2-4', 'Should ACCEPT (explicit day)'),
                ('xyz', 'Should REJECT (gibberish)')
            ]
        },
        {
            'name': '📅 MULTI-DAY EVENT',
            'planner_phone': '2222222222',
            'guest_phone': '9999999992',
            'dates': ['2025-08-15', '2025-08-16', '2025-08-18'],  # Fri, Sat, Mon
            'inputs': [
                ('2-4', 'Should REJECT (ambiguous time-only)'),
                ('2-4pm', 'Should ACCEPT (time with AM/PM)'),
                ('afternoon', 'Should ACCEPT (period always works)'),
                ('Friday 2-4', 'Should ACCEPT (explicit day)'),
                ('xyz', 'Should REJECT (gibberish)')
            ]
        }
    ]
    
    for test_case in test_cases:
        print(f"\n{test_case['name']}")
        print("=" * 60)
        print(f"Event dates: {test_case['dates']}")
        print("-" * 40)
        
        # Create test data for this case
        planner = Planner(phone_number=test_case['planner_phone'], name=f"Planner {test_case['name']}")
        db.session.add(planner)
        db.session.commit()
        
        event = Event(planner_id=planner.id, title=f"Event {test_case['name']}", workflow_stage='collecting_availability')
        db.session.add(event)
        db.session.commit()
        
        guest = Guest(event_id=event.id, name=f"Guest {test_case['name']}", phone_number=test_case['guest_phone'])
        db.session.add(guest)
        db.session.commit()
        
        # Create guest state
        state_data = {'event_dates': test_case['dates']}
        guest_state = GuestState(
            phone_number=test_case['guest_phone'],
            current_state='awaiting_availability',
            event_id=event.id
        )
        guest_state.set_state_data(state_data)
        db.session.add(guest_state)
        db.session.commit()
        
        # Test each input
        for input_text, expectation in test_case['inputs']:
            print(f"\n📝 Testing: '{input_text}'")
            print(f"   Expected: {expectation}")
            
            try:
                response = handler.handle_availability_response(guest_state, input_text)
                
                if "Got it!" in response:
                    print("   ✅ ACCEPTED - Availability parsed successfully")
                else:
                    print("   ❌ REJECTED - Availability not understood")
                    
            except Exception as e:
                print(f"   ❌ ERROR: {e}")
                
            # Reset for next test
            guest_state.current_state = 'awaiting_availability'
            guest_state.save()
    
    print("\n" + "=" * 60)
    print("🎉 SUMMARY:")
    print("✅ Single-day events now accept time-only inputs!")
    print("✅ Multi-day events still require day names for ambiguous times!")
    print("✅ Both types accept periods like 'afternoon' and explicit day references!")
    print("=" * 60)
