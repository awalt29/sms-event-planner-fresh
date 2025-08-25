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

print('🧪 Testing Add Guest After Overlap Calculation')
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
    
    # Mock the send_availability_request
    original_send = guest_service.send_availability_request
    sent_requests = []
    
    def mock_send_availability_request(guest):
        sent_requests.append(guest)
        print(f"   📤 MOCK: Availability request sent to {guest.name}")
        return True
    
    guest_service.send_availability_request = mock_send_availability_request
    
    # Create handler
    handler = AddGuestHandler(event_service, guest_service, message_service, ai_service, availability_service)
    
    # Test scenario: Add guest after overlaps were calculated
    print(f"\n📋 Test: Adding Guest After Overlap Calculation")
    print(f"   Scenario: Planner was in time selection, adds new guest")
    
    # Create event in time selection stage (overlaps calculated)
    event = Event(
        planner_id=planner.id,
        title="Test Event",
        workflow_stage='adding_guest',
        previous_workflow_stage='selecting_time'
    )
    # Simulate that overlaps were calculated by setting available_windows
    event.available_windows = '[{"date": "2025-08-20", "start_time": "2pm", "end_time": "4pm"}]'
    db.session.add(event)
    db.session.commit()
    
    # Add existing guest with availability
    existing_guest = Guest(
        event_id=event.id,
        name='John',
        phone_number='+15551234567',
        availability_provided=True
    )
    db.session.add(existing_guest)
    db.session.commit()
    
    # Clear the sent requests tracker
    sent_requests.clear()
    
    try:
        # Test adding a new guest
        guest_input = "Sarah 555-987-6543"
        result = handler.handle_message(event, guest_input)
        
        print(f"   ✅ Result stage: {result.new_stage}")
        print(f"   ✅ Availability request sent: {len(sent_requests) > 0}")
        
        # Check if the message includes availability status with options
        if "Press 1 to view current overlaps" in result.message:
            print(f"   ✅ PERFECT: Message includes 'Press 1 to view current overlaps' option!")
        else:
            print(f"   ❌ MISSING: Should include overlap viewing option")
            
        if "I'll recalculate everyone's availability once they respond" in result.message:
            print(f"   ✅ GOOD: Mentions recalculation")
        else:
            print(f"   ❌ MISSING: Should mention recalculation")
            
        if result.new_stage == 'tracking_availability':
            print(f"   ✅ CORRECT: Returns to tracking_availability stage")
        else:
            print(f"   ❌ WRONG: Should return to tracking_availability, got {result.new_stage}")
        
        print(f"\n   📱 Full Response:")
        print(f"   {result.message}")
        
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    # Clean up
    db.session.delete(existing_guest)
    db.session.delete(event)
    db.session.delete(planner)
    db.session.commit()
    
    print(f"\n{'='*60}")
    print("🎯 EXPECTED RESULT:")
    print("✅ Guest added and availability request sent")
    print("✅ Returns to tracking_availability stage")
    print("✅ Message includes 'Press 1 to view current overlaps' option")
    print("✅ Mentions that availability will be recalculated")
    print(f"{'='*60}")
