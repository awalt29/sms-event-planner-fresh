import sys
sys.path.append('.')

from app import create_app, db
from app.models.event import Event
from app.models.planner import Planner
from app.models.guest import Guest
from app.handlers.add_guest_handler import AddGuestHandler
from app.services.ai_processing_service import AIProcessingService
from app.services.event_workflow_service import EventWorkflowService
from app.services.guest_management_service import GuestManagementService
from app.services.message_formatting_service import MessageFormattingService
from app.services.availability_service import AvailabilityService
from unittest.mock import Mock

print('🧪 Testing Add Guest Availability Request Fix')
print('=' * 60)

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
    
    # Create services with mocking for send_availability_request
    ai_service = AIProcessingService()
    event_service = EventWorkflowService()
    guest_service = GuestManagementService()
    message_service = MessageFormattingService()
    availability_service = AvailabilityService()
    
    # Mock the send_availability_request to track if it's called
    original_send = guest_service.send_availability_request
    sent_requests = []
    
    def mock_send_availability_request(guest):
        sent_requests.append(guest)
        print(f"   📤 MOCK: Availability request sent to {guest.name} ({guest.phone_number})")
        return True
    
    guest_service.send_availability_request = mock_send_availability_request
    
    # Create handler
    handler = AddGuestHandler(event_service, guest_service, message_service, ai_service, availability_service)
    
    # Test scenarios where availability requests should be sent
    test_scenarios = [
        {
            'name': 'During Availability Collection',
            'current_stage': 'adding_guest',
            'previous_stage': 'collecting_availability',
            'should_send': True,
            'description': 'User added guest while in availability collection phase'
        },
        {
            'name': 'During Availability Tracking',
            'current_stage': 'adding_guest', 
            'previous_stage': 'tracking_availability',
            'should_send': True,
            'description': 'User added guest while tracking availability responses'
        },
        {
            'name': 'From Confirmation Menu',
            'current_stage': 'adding_guest',
            'previous_stage': 'awaiting_confirmation', 
            'should_send': False,
            'description': 'User added guest from confirmation menu (event planning complete)'
        },
        {
            'name': 'After Time Selection',
            'current_stage': 'adding_guest',
            'previous_stage': 'selecting_time',
            'should_send': True,
            'description': 'User added guest after time was selected (needs recalculation)'
        }
    ]
    
    for i, scenario in enumerate(test_scenarios):
        print(f"\n📋 Test {i+1}: {scenario['name']}")
        print(f"   Description: {scenario['description']}")
        print(f"   Previous Stage: {scenario['previous_stage']}")
        print(f"   Should Send Request: {scenario['should_send']}")
        
        # Create event for this test
        event = Event(
            planner_id=planner.id,
            title=f"Test Event {i+1}",
            workflow_stage=scenario['current_stage'],
            previous_workflow_stage=scenario['previous_stage']
        )
        db.session.add(event)
        db.session.commit()
        
        # Clear the sent requests tracker
        sent_requests.clear()
        
        try:
            # Test adding a guest
            guest_input = f"TestGuest{i+1} 555000000{i+1}"
            result = handler.handle_message(event, guest_input)
            
            # Check if availability request was sent
            request_sent = len(sent_requests) > 0
            
            if request_sent == scenario['should_send']:
                print(f"   ✅ CORRECT: Request sent = {request_sent}")
                if request_sent:
                    print(f"   📤 Sent to: {sent_requests[0].name}")
                
                if "I've sent them an availability request" in result.message:
                    print(f"   ✅ CORRECT: Message mentions availability request")
                elif not scenario['should_send']:
                    print(f"   ✅ CORRECT: Message doesn't mention availability request")
                else:
                    print(f"   ❌ WARNING: Message should mention availability request")
                    
            else:
                print(f"   ❌ WRONG: Expected request sent = {scenario['should_send']}, got {request_sent}")
                
            print(f"   Response: {result.message[:100]}...")
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
        
        # Clean up
        db.session.delete(event)
        db.session.commit()
    
    print("\n" + "=" * 60)
    print("🎯 SUMMARY:")
    print("Fixed the logic to send availability requests based on PREVIOUS stage")
    print("not current 'adding_guest' stage. This ensures guests get availability")
    print("requests when added during availability collection phases!")
    print("=" * 60)
