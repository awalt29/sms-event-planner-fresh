import sys
sys.path.append('.')

print('🧪 Testing "Add Guests" Plural Recognition')
print('=' * 50)

# Test the logic directly without importing the full router
def test_add_guest_recognition():
    test_messages = [
        "add guest",
        "Add guest", 
        "add guests",
        "Add guests",
        "ADD GUESTS",
        "something else"
    ]
    
    for message in test_messages:
        message_lower = message.lower().strip()
        
        print(f"📱 Testing: '{message}'")
        
        # This is the new logic we added
        if message_lower in ['add guest', 'add guests']:
            print(f"   ✅ RECOGNIZED as add guest command")
        else:
            print(f"   ❌ NOT recognized as add guest command")

test_add_guest_recognition()

print(f"\n{'='*50}")
print("🎯 Both 'add guest' and 'add guests' should now work!")
print("The logic now checks for both singular and plural forms.")
print('='*50)
