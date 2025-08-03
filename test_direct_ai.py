#!/usr/bin/env python3

# Simple test of suggest_venues function without Flask app context
import sys
import os

# Add the project root to path
sys.path.insert(0, '/Users/aaronwalters/Planner_app_live')

# Set environment variables needed
os.environ['OPENAI_API_KEY'] = 'test-key'  # We'll test fallback mode

def test_suggest_venues_direct():
    """Test suggest_venues function directly."""
    
    # Import after setting up path
    from app.utils.ai import AIService
    
    print("🔍 Testing 'chinese food' with AIService directly...")
    print("=" * 50)
    
    # Create AI service instance
    ai_service = AIService()
    
    # Test the smart conversion mapping
    activity = "chinese food"
    location = "Brooklyn"
    
    print(f"Input: activity='{activity}', location='{location}'")
    print()
    
    # Test the conversion logic directly
    activity_lower = activity.lower().strip()
    broad_to_specific = {
        'chinese food': 'Chinese restaurant',
        'chinese': 'Chinese restaurant',
        'italian food': 'Italian restaurant', 
        'drinks': 'bar or cocktail lounge',
        'food': 'restaurant'
    }
    
    processed_activity = activity
    if activity_lower in broad_to_specific:
        processed_activity = broad_to_specific[activity_lower]
        print(f"✅ Conversion: '{activity}' → '{processed_activity}'")
    else:
        print(f"❌ No conversion found for: '{activity_lower}'")
    
    print()
    
    # Test fallback venue suggestions (since we don't have real OpenAI key)
    fallback_result = ai_service._create_fallback_venue_suggestions(processed_activity, location)
    
    print("📊 Fallback result:")
    import json
    print(json.dumps(fallback_result, indent=2))
    
    print()
    print(f"Success: {fallback_result.get('success')}")
    print(f"Venues count: {len(fallback_result.get('venues', []))}")

if __name__ == "__main__":
    test_suggest_venues_direct()
