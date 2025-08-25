import sys
sys.path.append('.')

from app import create_app
from app.handlers.guest_collection_handler import GuestCollectionHandler
from app.services.ai_processing_service import AIProcessingService
from app.services.event_workflow_service import EventWorkflowService
from app.services.guest_management_service import GuestManagementService
from app.services.message_formatting_service import MessageFormattingService

print('🧪 Testing Enhanced Guest Number Parsing')
print('=' * 50)

app = create_app()

with app.app_context():
    # Create handler
    ai_service = AIProcessingService()
    event_service = EventWorkflowService()
    guest_service = GuestManagementService()
    message_service = MessageFormattingService()
    
    handler = GuestCollectionHandler(event_service, guest_service, message_service, ai_service)
    
    # Test various phone number formats
    test_inputs = [
        "Aaron(9145606464)",           # From screenshot - parentheses format
        "John 5105935336",             # Standard format
        "Mary Smith, 111-555-1234",    # With comma separator
        "Bob(555) 123-4567",           # Parentheses with spaces
        "Lisa:555-123-4567",           # With colon separator
        "Tom - 555.123.4567",          # With dash separator
        "Sarah 555 123 4567",          # Spaces in phone
        "Mike(555)1234567",            # Parentheses no spaces
        "555-123-4567 Alice",          # Phone first
        "Kate Johnson (555) 987-6543", # Full format
        "David(9145606464",            # Missing closing paren
        "NoPhoneHere",                 # No phone number
        "Rachel and Tom"               # Multiple names no phone
    ]
    
    print("Testing various guest input formats:")
    print("-" * 50)
    
    for input_text in test_inputs:
        print(f"\n📝 Testing: '{input_text}'")
        
        try:
            # Test AI parsing
            ai_result = handler._ai_parse_guest(input_text)
            print(f"   AI Result: {ai_result}")
            
            # Test regex parsing
            regex_result = handler._regex_parse_guest(input_text)
            print(f"   Regex Result: {regex_result}")
            
            # Test combined parsing (what the handler actually uses)
            combined_result = handler._parse_guest_input(input_text)
            print(f"   Combined Result: {combined_result}")
            
            if combined_result and combined_result.get('success'):
                guests = combined_result.get('guests', [])
                if guests:
                    guest = guests[0]
                    print(f"   ✅ SUCCESS: Name='{guest['name']}', Phone='{guest['phone']}'")
                else:
                    print("   ❌ SUCCESS but no guests found")
            else:
                error = combined_result.get('error', 'Unknown error') if combined_result else 'No result'
                print(f"   ❌ FAILED: {error}")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
    
    print("\n" + "=" * 50)
    print("Summary: Enhanced parsing should handle more number formats!")
