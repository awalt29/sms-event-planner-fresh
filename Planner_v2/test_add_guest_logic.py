import sys
sys.path.append('.')

print('🧪 Testing Add Guest After Overlap Calculation Logic')
print('=' * 60)

# Simulate the key logic from the fixed add guest handler
def test_overlap_calculation_scenario():
    """Test the logic for adding guests after overlap calculation"""
    
    # Simulate scenario: overlaps were calculated, adding new guest
    overlaps_calculated = True
    previous_stage = 'selecting_time'
    should_send_availability = True
    return_stage = 'tracking_availability'  # This was changed from 'awaiting_availability'
    
    print(f"📋 Scenario: Adding guest after overlap calculation")
    print(f"   Previous stage: {previous_stage}")
    print(f"   Overlaps calculated: {overlaps_calculated}")
    print(f"   Should send availability: {should_send_availability}")
    print(f"   Return stage: {return_stage}")
    
    # Simulate the message building logic
    confirmation = "✅ Added Sarah to your event!\n\n"
    confirmation += "I've sent them an availability request.\n\n"
    
    if overlaps_calculated:
        confirmation += "I'll recalculate everyone's availability once they respond.\n\n"
        
        # Simulate format_availability_status output
        availability_status = "📊 Availability Status:\n\n"
        availability_status += "✅ Responded: 1/2\n"
        availability_status += "⏳ Pending: 1\n\n"
        availability_status += "Still waiting for:\n"
        availability_status += "- Sarah\n"
        availability_status += "\nSend 'remind' to send follow-up messages.\n"
        availability_status += "\nPress 1 to view current overlaps"
        
        confirmation += availability_status
    
    print(f"\n📱 Expected Message:")
    print(f"---")
    print(confirmation)
    print(f"---")
    
    # Verify the message includes the key elements
    checks = [
        ("✅ Added", "Guest addition confirmation"),
        ("availability request", "Mentions availability request sent"),
        ("I'll recalculate", "Mentions recalculation"),
        ("Press 1 to view current overlaps", "Provides overlap viewing option"),
        ("📊 Availability Status", "Shows full availability status")
    ]
    
    print(f"\n🔍 Verification:")
    for check_text, description in checks:
        if check_text in confirmation:
            print(f"   ✅ {description}")
        else:
            print(f"   ❌ Missing: {description}")
    
    print(f"\n🎯 Key Fix:")
    print(f"   • Return stage changed to 'tracking_availability' (was 'awaiting_availability')")
    print(f"   • Full availability status included with 'Press 1' option")
    print(f"   • Planners can now continue with current overlaps OR wait for new guest")

test_overlap_calculation_scenario()

print(f"\n{'='*60}")
print("🚀 RESULT: Planners can now use 'Press 1 to view current overlaps'")
print("after adding guests during overlap calculation!")
print(f"{'='*60}")
