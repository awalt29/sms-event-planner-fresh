#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, '/Users/aaronwalters/Planner_app_live')

from app import create_app
from app.utils.ai import suggest_venues
import logging

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_chinese_food_debug():
    """Debug why 'chinese food' might not be working."""
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        print("🔍 Testing 'chinese food' venue suggestions...")
        print("=" * 50)
        
        # Test the exact call that would happen in SMS flow
        activity = "chinese food"
        location = "New York"
        
        print(f"Input: activity='{activity}', location='{location}'")
        print()
        
        try:
            # Call suggest_venues exactly as SMS flow does
            result = suggest_venues(activity, location)
            
            print("📊 Result structure:")
            print(f"Type: {type(result)}")
            print(f"Keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            print()
            
            print("🎯 Full result:")
            import json
            print(json.dumps(result, indent=2))
            print()
            
            # Check the specific condition from SMS flow
            has_success = result.get('success')
            print(f"❓ result.get('success'): {has_success}")
            print(f"❓ Type of 'success' value: {type(has_success)}")
            
            if has_success:
                venues = result.get('venues', [])
                print(f"✅ Success! Found {len(venues)} venues")
                
                for i, venue in enumerate(venues, 1):
                    print(f"{i}. {venue.get('name', 'Unknown')}")
                    print(f"   Description: {venue.get('description', 'None')}")
                    print(f"   Link: {venue.get('link', 'None')}")
                    print()
            else:
                print(f"❌ Success is falsy: {repr(has_success)}")
                error = result.get('error', 'No error message')
                print(f"Error: {error}")
                
        except Exception as e:
            print(f"💥 Exception occurred: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_chinese_food_debug()
