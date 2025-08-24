import sys
sys.path.append('.')

from app import create_app, db
from app.models.event import Event
from app.models.planner import Planner
from app.routes.sms import SMSRouter
from app.services.ai_processing_service import AIProcessingService
from app.services.event_workflow_service import EventWorkflowService
from app.services.guest_management_service import GuestManagementService
from app.services.message_formatting_service import MessageFormattingService
from app.services.availability_service import AvailabilityService

print('🧪 Testing "Add Guests" Plural Recognition')
print('=' * 50)

app = create_app()

with app.app_context():
    # Clean up any existing test data
    planner = Planner.query.filter_by(phone_number='1234567890').first()
    if planner:
        Event.query.filter_by(planner_id=planner.id).delete()
        db.session.delete(planner)
        db.session.commit()
    
    # Create test planner
    planner = Planner(phone_number='1234567890', name='Test User')
    db.session.add(planner)
    db.session.commit()
    
    # Create test event
    event = Event(
        planner_id=planner.id,
        title="Test Event",
        workflow_stage='collecting_availability',
        previous_workflow_stage='collecting_guests'
    )
    db.session.add(event)
    db.session.commit()
    
    # Create services
    ai_service = AIProcessingService()
    event_service = EventWorkflowService()
    guest_service = GuestManagementService()
    message_service = MessageFormattingService()
    availability_service = AvailabilityService()
    
    # Create SMS router
    router = SMSRouter(ai_service, event_service, guest_service, message_service, availability_service)
    
    # Test both variations
    test_messages = [
        "add guest",
        "Add guest", 
        "add guests",
        "Add guests",
        "ADD GUESTS"
    ]
    
    for message in test_messages:
        print(f"\n📱 Testing: '{message}'")
        try:
            response = router.route_message(planner.phone_number, message)
            
            if "Who would you like to add to this event?" in response:
                print(f"   ✅ RECOGNIZED as add guest command")
            else:
                print(f"   ❌ NOT recognized as add guest command")
                print(f"   Response: {response[:100]}...")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
    
    # Clean up
    db.session.delete(event)
    db.session.delete(planner)
    db.session.commit()
    
    print(f"\n{'='*50}")
    print("🎯 Both 'add guest' and 'add guests' should now work!")
    print("Users can type either singular or plural form.")
    print('='*50)
