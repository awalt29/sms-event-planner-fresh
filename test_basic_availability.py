import sys
sys.path.append('.')

from app import create_app
from app.handlers.guest_availability_handler import GuestAvailabilityHandler
from app.services.ai_processing_service import AIProcessingService
from app.services.event_workflow_service import EventWorkflowService
from app.services.guest_management_service import GuestManagementService
from app.services.message_formatting_service import MessageFormattingService

print('🧪 Testing Guest Availability Validation')
print('=' * 50)

app = create_app()

with app.app_context():
    # Create required services
    ai_service = AIProcessingService()
    event_service = EventWorkflowService()
    guest_service = GuestManagementService()
    message_service = MessageFormattingService()
    
    handler = GuestAvailabilityHandler(event_service, guest_service, message_service, ai_service)
    
    test_inputs = [
        "Friday from 2-4",
        "Friday 2-4", 
        "Friday 2-4pm",
        "Friday 2pm-4pm",
        "Friday 2-4 pm",
        "friday 2-4pm",
        "Saturday all day",
        "Monday afternoon"
    ]
    
    print("Testing validation patterns:")
    print("-" * 30)
    
    for input_text in test_inputs:
        is_valid = handler._is_valid_availability_input(input_text)
        status = "✅ VALID" if is_valid else "❌ INVALID"
        print(f"{status}: '{input_text}'")
    
    print("\nTesting simple parsing for failed inputs:")
    print("-" * 40)
    
    failed_inputs = [
        "Friday from 2-4",
        "Friday 2-4", 
        "Friday 2-4pm"
    ]
    
    for input_text in failed_inputs:
        simple_result = handler._simple_parse_availability(input_text)
        print(f"Input: '{input_text}'")
        print(f"Simple parse result: {simple_result}")
        print("-" * 20)
