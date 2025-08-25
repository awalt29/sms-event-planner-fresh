import sys
sys.path.append('.')

from app import create_app
from app.handlers.guest_collection_handler import GuestCollectionHandler
from app.services.ai_processing_service import AIProcessingService
from app.services.event_workflow_service import EventWorkflowService
from app.services.guest_management_service import GuestManagementService
from app.services.message_formatting_service import MessageFormattingService

print('🧪 Testing Key Guest Parsing Formats')
print('=' * 50)

app = create_app()

with app.app_context():
    # Create handler
    ai_service = AIProcessingService()
    event_service = EventWorkflowService()
    guest_service = GuestManagementService()
    message_service = MessageFormattingService()
    
    handler = GuestCollectionHandler(event_service, guest_service, message_service, ai_service)
    
    # Test key formats from the screenshot issue
    test_inputs = [
        "Aaron(9145606464)",           # Main issue from screenshot
        "Bob(555) 123-4567",           # Parentheses with spaces
        "Mike(555)1234567",            # Parentheses compound format
    ]
    
    print("Testing key problematic formats:")
    print("-" * 40)
    
    for input_text in test_inputs:
        print(f"\n📝 Testing: '{input_text}'")
        
        try:
            # Test regex parsing only (since AI is having issues)
            regex_result = handler._regex_parse_guest(input_text)
            print(f"   Regex Result: {regex_result}")
            
            if regex_result and regex_result.get('success'):
                guests = regex_result.get('guests', [])
                if guests:
                    guest = guests[0]
                    print(f"   ✅ SUCCESS: Name='{guest['name']}', Phone='{guest['phone']}'")
                else:
                    print("   ❌ SUCCESS but no guests found")
            else:
                error = regex_result.get('error', 'Unknown error') if regex_result else 'No result'
                print(f"   ❌ FAILED: {error}")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
    
    print("\n" + "=" * 40)
    print("These are the main formats from the user's screenshot issue.")
