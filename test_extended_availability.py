import sys
sys.path.append('.')

from app import create_app
from app.handlers.guest_availability_handler import GuestAvailabilityHandler
from app.services.ai_processing_service import AIProcessingService
from app.services.event_workflow_service import EventWorkflowService
from app.services.guest_management_service import GuestManagementService
from app.services.message_formatting_service import MessageFormattingService

print('🧪 Testing Extended Availability Validation')
print('=' * 50)

app = create_app()

with app.app_context():
    # Create required services
    ai_service = AIProcessingService()
    event_service = EventWorkflowService()
    guest_service = GuestManagementService()
    message_service = MessageFormattingService()
    
    handler = GuestAvailabilityHandler(event_service, guest_service, message_service, ai_service)
    
    # Test various input formats that should work
    valid_inputs = [
        # Original working patterns
        "Friday 2-4pm",
        "Saturday all day", 
        "Monday afternoon",
        "Tuesday after 3pm",
        
        # Newly fixed patterns
        "Friday from 2-4",
        "Friday 2-4",
        "Monday from 9am-5pm",
        "Wednesday 10-12",
        
        # Edge cases
        "Sat 2-4",
        "fri from 2-4pm",
        "Sunday from 1-3",
        "Thursday 9-17",  # 24-hour format
        "morning",
        "2-4pm",
        "from 2-4pm"
    ]
    
    # Test gibberish that should fail
    invalid_inputs = [
        "xyz",
        "asdfghjkl",
        "maybe",
        "I don't know",
        "call me",
        "123456",
        "",
        "   "
    ]
    
    print("✅ Should be VALID:")
    print("-" * 20)
    for input_text in valid_inputs:
        is_valid = handler._is_valid_availability_input(input_text)
        status = "✅" if is_valid else "❌"
        print(f"{status} '{input_text}'")
    
    print("\n❌ Should be INVALID:")
    print("-" * 20)
    for input_text in invalid_inputs:
        is_valid = handler._is_valid_availability_input(input_text)
        status = "✅" if not is_valid else "❌"  # Reverse logic - we want these to be invalid
        print(f"{status} '{input_text}'")
